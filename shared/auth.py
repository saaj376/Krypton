import secrets
import string
from .database import create_key, validate_key, delete_expired_keys

def generate_secure_key(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def issue_key(owner_name: str, ttl_hours: int = 3) -> str:
    key_string = generate_secure_key()
    create_key(key_string, owner_name, ttl_hours)
    return key_string

def verify_access(key_string: str) -> bool:
    delete_expired_keys()
    return validate_key(key_string)
