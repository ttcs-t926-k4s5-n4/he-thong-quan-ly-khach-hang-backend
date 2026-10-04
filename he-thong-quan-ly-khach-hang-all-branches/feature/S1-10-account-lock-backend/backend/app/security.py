import hashlib
import hmac
import os
import secrets
import time

from fastapi import HTTPException, Response

SESSION_TTL = int(os.getenv("SESSION_TTL", "900"))


def now() -> int:
    return int(time.time())


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        260_000,
    )
    return f"pbkdf2_sha256$260000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        method, rounds, salt, digest = stored.split("$")
        if method != "pbkdf2_sha256":
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(rounds),
        )
        return hmac.compare_digest(candidate, bytes.fromhex(digest))
    except (ValueError, AttributeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_session_cookie(
    response: Response,
    token: str,
    secure: bool,
) -> None:
    response.set_cookie(
        "session",
        token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=SESSION_TTL,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie("session", path="/")


def unauthorized(message: str) -> None:
    raise HTTPException(status_code=401, detail=message)
