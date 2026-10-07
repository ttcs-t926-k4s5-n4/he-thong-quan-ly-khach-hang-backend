import hashlib
import hmac
import secrets

ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iters, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(digest.hex(), expected)
    except Exception:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def password_error(password: str) -> str | None:
    if len(password) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự, có ít nhất một chữ và một số."
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return "Mật khẩu mới phải có ít nhất 8 ký tự, có ít nhất một chữ và một số."
    return None
