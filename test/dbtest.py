import sys
import os
import time

# Add project root to path so we can import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import init_db, create_key, validate_key, delete_expired_keys, get_connection

def test_key_lifecycle():
    print("--- Testing Key Lifecycle ---")
    
    # 1. Initialize
    init_db()
    
    # 2. Create a valid key (3 hours)
    key_valid = "valid-key-123"
    create_key(key_valid, "Tester A", ttl_hours=3)
    
    # 3. Create an expired key (expired 1 hour ago)
    key_expired = "expired-key-456"
    create_key(key_expired, "Tester B", ttl_hours=-1) 
    
    # 4. Validate
    print(f"Validating '{key_valid}': {validate_key(key_valid)} (Expected: True)")
    print(f"Validating '{key_expired}': {validate_key(key_expired)} (Expected: False)")
    
    # 5. Cleanup
    print("Running cleanup...")
    delete_expired_keys()
    
    # 6. Verify cleanup
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key_string FROM api_keys")
        keys = [row[0] for row in cursor.fetchall()]
        print(f"Remaining keys: {keys} (Expected: ['{key_valid}'])")

def test_database_persistence():
    print("\n--- Testing Persistence ---")
    # Re-connect to ensure data is still there
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM api_keys")
        row = cursor.fetchone()
        if row:
            count = row[0]
            print(f"Key count after reconnect: {count}")
        else:
            print("No keys found.")

if __name__ == "__main__":
    test_key_lifecycle()
    test_database_persistence()
