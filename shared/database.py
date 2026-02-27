import sqlite3
import os
from datetime import datetime, timedelta, timezone

# Ensure DB is in the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "krypton.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

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

def create_key(key_string: str, owner_name: str, ttl_hours: int = 3):
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO api_keys (key_string, owner_name, expires_at, is_active)
            VALUES (?, ?, ?, ?)
        ''', (key_string, owner_name, expires_at.isoformat(), True))
        conn.commit()
    print(f"Key created for {owner_name}: {key_string} (Expires: {expires_at})")

def validate_key(key_string: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT expires_at, is_active FROM api_keys 
            WHERE key_string = ?
        ''', (key_string,))
        row = cursor.fetchone()
        
        if not row:
            return False
            
        expires_at_str, is_active = row
        
        if not is_active:
            return False

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            return False
            
        if datetime.now(timezone.utc) > expires_at:
            return False
            
        return True

def delete_expired_keys():
    now_str = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM api_keys WHERE expires_at < ?', (now_str,))
        deleted_count = cursor.rowcount
        conn.commit()

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
        
if __name__ == "__main__":
    init_db()