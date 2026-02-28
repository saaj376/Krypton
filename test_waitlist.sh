#!/bin/bash
# test_waitlist.sh (Optional Script)
# Tests the Krypton Gateway waitlist enforcement by simulating 3 users joining at the same time.

echo "======================================================"
echo "   KRYPTON SDK - OPTIONAL WAITLIST ENFORCEMENT TEST"
echo "======================================================"
echo ""
echo "⚠️  REQUIREMENT: Local gateway must be running at http://127.0.0.1:8000"
echo "   (If it is not running, run './start_krypton.sh' first)"
echo ""

# Check if the server is accessible
if ! curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "❌ Error: Could not connect to the local gateway."
    echo "Please ensure the server is running."
    exit 1
fi

echo "--- 1. Resetting Database (Clearing Active Keys & Waitlist) ---"
python3 -c "import sqlite3; conn = sqlite3.connect('krypton.db'); cursor = conn.cursor(); cursor.execute('DELETE FROM api_keys'); cursor.execute('DELETE FROM waitlist'); conn.commit()"
if [ $? -eq 0 ]; then
    echo "✅ Database cleared. Active users currently: 0"
else
    echo "❌ Failed to reset database."
    exit 1
fi
echo ""

echo "--- 2. Simulating 3 Concurrent Users Joining the Queue ---"
echo "Note: The RTX 3050 limit allows 2 active users at maximum."
echo ""

# Function to simulate a user request and extract JSON fields nicely using Python
simulate_user() {
    local email=$1
    local user_num=$2
    sleep 1 # Stagger slightly just to ensure sequential DB allocation order for clarity
    
    echo "> [User $user_num] Requesting access for $email..."
    
    response=$(curl -s -X 'POST' \
      'http://127.0.0.1:8000/join-queue' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d "{\"user_email\": \"$email\"}")
      
    # Print the parsed response status beautifully
    python3 -c "
import json, sys
try:
    data = json.loads('''$response''')
    status = data.get('status', 'unknown')
    msg = data.get('message', '')
    api_key = data.get('api_key', 'N/A')
    
    if status == 'success':
        print(f'   ✅ SUCCESS! Granted API Key: {api_key}')
    elif status == 'waitlist':
        print(f'   ⏳ WAITLIST! Server full. Status: {status} | Message: {msg}')
    else:
        print(f'   ⚠️ UNEXPECTED: {data}')
except Exception as e:
    print(f'   ❌ Could not parse JSON response: {e}')
"
}

# Run simulated users sequentially to guarantee ordered testing output
simulate_user "tester1@example.com" 1
simulate_user "tester2@example.com" 2
simulate_user "tester3@example.com" 3

echo ""
echo "--- Results Expected ---"
echo "Users 1 and 2 should have received a 'SUCCESS' since capacity is 2."
echo "User 3 should have received 'WAITLIST'."
echo "======================================================"
