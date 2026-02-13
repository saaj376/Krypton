import sqlite3
import os
from datetime import datetime, timedelta

# Ensure DB is in the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "krypton.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the SQLite database with the new schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Dropping table to allow schema update since we are in dev/prototype phase
        cursor.execute("DROP TABLE IF EXISTS api_keys") 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                key_string TEXT PRIMARY KEY,
                owner_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        conn.commit()
    print(f"Database initialized at {DB_PATH}")

def create_key(key_string: str, owner_name: str, ttl_hours: int = 3):
    """Create a new API key with expiration."""
    # Calculate expiration time in Python to ensure ISO format compatibility
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO api_keys (key_string, owner_name, expires_at, is_active)
            VALUES (?, ?, ?, ?)
        ''', (key_string, owner_name, expires_at, True))
        conn.commit()
    print(f"Key created for {owner_name}: {key_string} (Expires: {expires_at})")

def validate_key(key_string: str) -> bool:
    """
    Check if the key exists, is active, and has not expired.
    Returns: True if valid, False otherwise.
    """
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
        
        # Convert string back to datetime for comparison
        # SQLite stores as string usually: "YYYY-MM-DD HH:MM:SS.ssssss"
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            # Fallback for simple format if needed
             expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S.%f")

        if not is_active:
            return False
            
        if datetime.utcnow() > expires_at:
            return False
            
        return True

def delete_expired_keys():
    """Delete keys that have passed their expiration time."""
    now = datetime.utcnow()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM api_keys WHERE expires_at < ?', (now,))
        deleted_count = cursor.rowcount
        conn.commit()
    print(f"Deleted {deleted_count} expired keys.")

if __name__ == "__main__":
    init_db()
