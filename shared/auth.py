import secrets
import string
from .database import create_key, validate_key, delete_expired_keys

def generate_secure_key(length=32):
    """Generate a random secure API key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def issue_key(owner_name: str, ttl_hours: int = 3) -> str:
    """Generate and store a new API key."""
    key_string = generate_secure_key()
    create_key(key_string, owner_name, ttl_hours)
    return key_string

def verify_access(key_string: str) -> bool:
    """Check if a key allows access. Deletes expired keys first."""
    # Lazy cleanup: delete expired keys on every check (or use a background task)
    delete_expired_keys()
    return validate_key(key_string)
