import time
import bcrypt
from fastapi import HTTPException

MAX_ATTEMPTS = 5
LOCKOUT_WINDOW = 15 * 60

def now():
    return int(time.time())

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False
