# Phase 2: Local GPU Gateway (The Engine)

This documentation explains how to update your local GPU Gateway (`v1_local/gateway.py`) and your shared database to handle active API keys, maximum concurrency, and the queue system automatically.

When you run `start_krypton.sh` after receiving an email from the Ping Server, this local system takes over all duties.

## 🚀 Step-by-Step Implementation Guide

### Step 1: Update the Database Schema & Functions
We need to modify `shared/database.py` to handle both active API keys and a waitlist for when your server is at maximum capacity (2 users).

1. Open `shared/database.py`.
2. Update the `init_db()` function to add the `waitlist` table:
   ```python
   def init_db():
       with get_connection() as conn:
           cursor = conn.cursor()
           # Existing api_keys table (ensure owner_name is treated as email)
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS api_keys (
                   key_string TEXT PRIMARY KEY,
                   owner_name TEXT NOT NULL, 
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   expires_at TEXT,
                   is_active BOOLEAN DEFAULT 1
               )
           ''')
           # NEW waitlist table
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS waitlist (
                   email TEXT PRIMARY KEY,
                   requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           ''')
           conn.commit()
   ```

3. Add these new helper functions to `shared/database.py`:
   ```python
   def count_active_keys() -> int:
       with get_connection() as conn:
           cursor = conn.cursor()
           now_str = datetime.now(timezone.utc).isoformat()
           cursor.execute('SELECT COUNT(*) FROM api_keys WHERE expires_at > ?', (now_str,))
           return cursor.fetchone()[0]

   def add_to_waitlist(email: str):
       with get_connection() as conn:
           cursor = conn.cursor()
           cursor.execute('INSERT OR IGNORE INTO waitlist (email) VALUES (?)', (email,))
           conn.commit()

   def pop_from_waitlist() -> str | None:
       with get_connection() as conn:
           cursor = conn.cursor()
           cursor.execute('SELECT email FROM waitlist ORDER BY requested_at ASC LIMIT 1')
           row = cursor.fetchone()
           if row:
               email = row[0]
               cursor.execute('DELETE FROM waitlist WHERE email = ?', (email,))
               conn.commit()
               return email
           return None
   ```

### Step 2: Set up Local Email Credentials
Your local server needs to send emails when users are added to the waitlist, when their key expires, or when they are promoted.

1. Create a `.env` file in the **root** of your `Krypton` folder (same level as `start_krypton.sh`).
2. Add the exact same credentials you used for the Ping Server:
   ```env
   SENDER_EMAIL=your_actual_email@gmail.com
   SENDER_APP_PASSWORD=the_16_char_password
   ```
*(Make sure to add `.env` to your global `.gitignore`!)*

### Step 3: Update `v1_local/gateway.py` with the Queue Logic
Open `v1_local/gateway.py` and import the new DB functions and email logic.

1. **Add the Email Sender Function:**
   Copy the `send_email` function from `ping_server/main.py` into `gateway.py` (or cleanly import it from a new `shared/email_utils.py` file if you prefer).

2. **Add the `/join-queue` Endpoint:**
   Create the endpoint the SDK will call when your server is ON.
   ```python
   import uuid
   from shared.database import count_active_keys, create_key, add_to_waitlist

   class QueueRequest(BaseModel):
       user_email: str

   @app.post("/join-queue")
   async def join_queue(req: QueueRequest):
       active_count = count_active_keys()
       
       if active_count < 2:
           # Server has room! Generate key immediately.
           new_api_key = f"kr_{uuid.uuid4().hex}"
           create_key(new_api_key, req.user_email, ttl_hours=3)
           
           # Email the user their key
           body = f"The server is free! Your API key is: {new_api_key}\nIt is valid for exactly 3 hours."
           send_email(req.user_email, "Your Krypton API Key", body)
           
           return {"status": "success", "api_key": new_api_key, "message": "API Key generated and emailed."}
       else:
           # Server is full. Add to waitlist.
           add_to_waitlist(req.user_email)
           body = "The Krypton Server is currently at max capacity (2 users). You have been added to the waitlist! We will email you your API key automatically when a slot opens."
           send_email(req.user_email, "Krypton Waitlist Confirmation", body)
           
           return {"status": "waitlist", "message": "Server at capacity. Added to waitlist."}
   ```

### Step 4: The Background Expiration Loop (The Enforcer)
This is the magic part. We will use FastAPI's lifespan (or background tasks) to check the database every 60 seconds, kick out expired users, and promote waitlisted users autonomously.

Add this code to `v1_local/gateway.py`:

```python
import asyncio
from contextlib import asynccontextmanager
from shared.database import get_connection, pop_from_waitlist
from datetime import datetime, timezone

async def enforce_expirations():
    while True:
        await asyncio.sleep(60) # Run every 60 seconds
        
        now_str = datetime.now(timezone.utc).isoformat()
        expired_emails = []
        
        # 1. Find and Delete Expired Keys
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT owner_name FROM api_keys WHERE expires_at < ?', (now_str,))
            rows = cursor.fetchall()
            
            for row in rows:
                expired_emails.append(row[0])
                
            if expired_emails:
                cursor.execute('DELETE FROM api_keys WHERE expires_at < ?', (now_str,))
                conn.commit()

        # 2. Email Expired Users
        for email in expired_emails:
            print(f"[ALERT] API Key for {email} has expired! Removing.")
            send_email(email, "Krypton Session Expired", "Your 3-hour session on Krypton has ended. Thank you for using the service!")

            # 3. Promote from Waitlist since a slot just opened!
            next_user = pop_from_waitlist()
            if next_user:
                new_key = f"kr_{uuid.uuid4().hex}"
                create_key(new_key, next_user, ttl_hours=3)
                print(f"[QUEUE] Promoted {next_user} from waitlist!")
                send_email(next_user, "Your Krypton API Key is Ready!", f"The server is free! Your turn. Here is your API key: {new_key}\n(Valid for 3 hours).")

# Start the background task when FastAPI starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background loop
    task = asyncio.create_task(enforce_expirations())
    yield
    # Shutdown: Cancel the loop
    task.cancel()

# Update your FastAPI initialization to include the lifespan:
# app = FastAPI(lifespan=lifespan)
```

### Step 5: Secure the `/generate` Endpoint
Finally, update your actual LLM endpoint so it rejects requests without a valid API Key.

1. Ensure the SDK client passes `X-API-Key` in the headers.
2. Update `v1_local/gateway.py` to use `Depends` to check the API key via `shared.database.validate_key()`.

You are now fully automated! When you run `start_krypton.sh`, the server will intelligently manage your 2-gpu limit, kick off hour expirations, and securely issue keys all by itself.
