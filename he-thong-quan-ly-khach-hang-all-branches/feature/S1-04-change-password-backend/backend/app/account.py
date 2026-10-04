import secrets
import time
from enum import Enum

from flask import current_app, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import hash_session_token, revoke_user_sessions
from app.db import fetch_one, get_db


class ChangePasswordResult(Enum):
    SUCCESS = "success"
    INVALID_NEW_PASSWORD = "invalid_new_password"
    WRONG_CURRENT_PASSWORD = "wrong_current_password"
    SESSION_EXPIRED = "session_expired"


def new_password_error(password: str) -> str | None:
    if len(password) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự."
    if len(password) > 128:
        return "Mật khẩu mới không được vượt quá 128 ký tự."
    if not any(character.isascii() and character.isalpha() for character in password):
        return "Mật khẩu mới phải có ít nhất một chữ cái."
    if not any(character.isascii() and character.isdigit() for character in password):
        return "Mật khẩu mới phải có ít nhất một chữ số."
    return None


def change_password(
    user_id: int,
    current_session_token: str,
    current_password: str,
    new_password: str,
) -> ChangePasswordResult:
    if new_password_error(new_password):
        return ChangePasswordResult.INVALID_NEW_PASSWORD

    connection = get_db()
    user = fetch_one(
        connection,
        """
        SELECT password_hash, credentials_version
        FROM dbo.users
        WHERE id = ?
        """,
        (user_id,),
    )

    if user is None or not check_password_hash(str(user["password_hash"]), current_password):
        return ChangePasswordResult.WRONG_CURRENT_PASSWORD

    password_hash = generate_password_hash(new_password, method="scrypt:32768:8:1")
    old_token_hash = hash_session_token(current_session_token)
    new_raw_token = secrets.token_urlsafe(32)
    new_token_hash = hash_session_token(new_raw_token)
    now = int(time.time())
    new_expires_at = now + int(current_app.config["LOGIN_SESSION_TTL_SECONDS"])
    old_credentials_version = int(user["credentials_version"])
    new_credentials_version = old_credentials_version + 1

    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE dbo.login_sessions
            SET token_hash = ?
            WHERE token_hash = ?
              AND user_id = ?
              AND credentials_version = ?
              AND revoked_at IS NULL
              AND expires_at > ?
            """,
            new_token_hash,
            old_token_hash,
            user_id,
            old_credentials_version,
            now,
        )

        if cursor.rowcount != 1:
            connection.rollback()
            return ChangePasswordResult.SESSION_EXPIRED

        cursor.execute(
            """
            UPDATE dbo.users
            SET password_hash = ?, credentials_version = ?, updated_at = ?
            WHERE id = ?
            """,
            password_hash,
            new_credentials_version,
            now,
            user_id,
        )

        revoke_user_sessions(connection, user_id, new_token_hash)

        cursor.execute(
            """
            UPDATE dbo.login_sessions
            SET credentials_version = ?, last_seen_at = ?, expires_at = ?
            WHERE token_hash = ?
            """,
            new_credentials_version,
            now,
            new_expires_at,
            new_token_hash,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    session["auth_token"] = new_raw_token
    session.permanent = True
    return ChangePasswordResult.SUCCESS
