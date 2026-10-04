import hashlib
import re
import secrets
import time
from enum import Enum

import pyodbc
from flask import current_app
from werkzeug.security import generate_password_hash

from app.db import fetch_one, get_db

GENERIC_RESET_MESSAGE = (
    "Nếu email đã được đăng ký, chúng tôi đã gửi liên kết đặt lại mật khẩu. "
    "Vui lòng kiểm tra hộp thư của bạn."
)
INVALID_LINK_MESSAGE = "Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng."
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ResetPasswordResult(Enum):
    SUCCESS = "success"
    INVALID_LINK = "invalid_link"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(normalize_email(email)))


def password_rule_error(password: str) -> str | None:
    if len(password) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự."
    if len(password) > 128:
        return "Mật khẩu mới không được vượt quá 128 ký tự."
    if not any(character.isascii() and character.isalpha() for character in password):
        return "Mật khẩu mới phải có ít nhất một chữ cái."
    if not any(character.isascii() and character.isdigit() for character in password):
        return "Mật khẩu mới phải có ít nhất một chữ số."
    return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_reset_url(token: str) -> str:
    base_url = str(current_app.config["FRONTEND_BASE_URL"]).rstrip("/")
    return f"{base_url}/reset-password/{token}"


def request_password_reset(email: str) -> str:
    normalized_email = normalize_email(email)
    connection = get_db()

    user = fetch_one(
        connection,
        """
        SELECT id, email
        FROM dbo.users
        WHERE LOWER(email) = LOWER(?)
        """,
        (normalized_email,),
    )

    # Không tiết lộ email có tồn tại hay không.
    if user is None:
        return GENERIC_RESET_MESSAGE

    user_id = int(user["id"])
    now = int(time.time())
    expires_at = now + int(current_app.config["RESET_TOKEN_TTL_SECONDS"])
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)

    cursor = connection.cursor()
    try:
        # Yêu cầu link mới sẽ vô hiệu hóa các link cũ chưa dùng.
        cursor.execute(
            """
            UPDATE dbo.password_reset_tokens
            SET used_at = ?
            WHERE user_id = ? AND used_at IS NULL
            """,
            now,
            user_id,
        )

        cursor.execute(
            """
            INSERT INTO dbo.password_reset_tokens (
                user_id,
                token_hash,
                expires_at,
                used_at,
                created_at
            )
            VALUES (?, ?, ?, NULL, ?)
            """,
            user_id,
            token_hash,
            expires_at,
            now,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    current_app.config["MAILER"].send_password_reset(
        str(user["email"]),
        build_reset_url(raw_token),
    )

    return GENERIC_RESET_MESSAGE


def inspect_reset_token(token: str) -> bool:
    now = int(time.time())
    row = fetch_one(
        get_db(),
        """
        SELECT id
        FROM dbo.password_reset_tokens
        WHERE token_hash = ?
          AND used_at IS NULL
          AND expires_at > ?
        """,
        (hash_token(token), now),
    )
    return row is not None


def reset_password(token: str, password: str) -> ResetPasswordResult:
    connection = get_db()
    now = int(time.time())
    token_hash = hash_token(token)
    password_hash = generate_password_hash(
        password,
        method="scrypt:32768:8:1",
    )

    cursor = connection.cursor()

    try:
        # UPDLOCK giúp 2 yêu cầu đồng thời không dùng cùng 1 token hai lần.
        cursor.execute(
            """
            SELECT id, user_id
            FROM dbo.password_reset_tokens WITH (UPDLOCK, ROWLOCK)
            WHERE token_hash = ?
              AND used_at IS NULL
              AND expires_at > ?
            """,
            token_hash,
            now,
        )
        row = cursor.fetchone()

        if row is None:
            connection.rollback()
            return ResetPasswordResult.INVALID_LINK

        reset_token_id = int(row[0])
        user_id = int(row[1])

        cursor.execute(
            """
            UPDATE dbo.users
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            password_hash,
            now,
            user_id,
        )

        cursor.execute(
            """
            UPDATE dbo.password_reset_tokens
            SET used_at = ?
            WHERE id = ? AND used_at IS NULL
            """,
            now,
            reset_token_id,
        )

        if cursor.rowcount != 1:
            connection.rollback()
            return ResetPasswordResult.INVALID_LINK

        connection.commit()
        return ResetPasswordResult.SUCCESS
    except pyodbc.Error:
        connection.rollback()
        raise
    except Exception:
        connection.rollback()
        raise
