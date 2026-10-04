"""
password.py — Đổi mật khẩu (S1-04) & Reset qua email (S1-03)
"""
import hashlib
import re
import secrets
import time
from enum import Enum

import pyodbc
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import hash_token, revoke_user_sessions
from app.db import fetch_one, get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

GENERIC_RESET_MSG = (
    "Nếu email đã được đăng ký, chúng tôi đã gửi liên kết đặt lại mật khẩu. "
    "Vui lòng kiểm tra hộp thư của bạn."
)
INVALID_LINK_MSG = "Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng."


class ChangePasswordResult(Enum):
    SUCCESS = "success"
    WRONG_CURRENT = "wrong_current"
    INVALID_NEW = "invalid_new"
    SESSION_EXPIRED = "session_expired"


class ResetPasswordResult(Enum):
    SUCCESS = "success"
    INVALID_LINK = "invalid_link"


# ── Validation helpers ────────────────────────────────────────────────────────

def password_rule_error(password: str) -> str | None:
    """Kiểm tra quy tắc mật khẩu: tối thiểu 8 ký tự, có chữ và số."""
    if len(password) < 8:
        return "Mật khẩu phải có ít nhất 8 ký tự."
    if len(password) > 128:
        return "Mật khẩu không được vượt quá 128 ký tự."
    if not any(c.isascii() and c.isalpha() for c in password):
        return "Mật khẩu phải có ít nhất một chữ cái."
    if not any(c.isascii() and c.isdigit() for c in password):
        return "Mật khẩu phải có ít nhất một chữ số."
    return None


# ── Change password (S1-04) ───────────────────────────────────────────────────

def change_password(
    user_id: int,
    current_session_raw: str,
    current_password: str,
    new_password: str,
) -> ChangePasswordResult:
    err = password_rule_error(new_password)
    if err:
        return ChangePasswordResult.INVALID_NEW

    conn = get_db()
    user = fetch_one(
        conn,
        "SELECT password_hash, credentials_version FROM dbo.users WHERE id=?",
        (user_id,),
    )
    if user is None or not check_password_hash(str(user["password_hash"]), current_password):
        return ChangePasswordResult.WRONG_CURRENT

    now = int(time.time())
    ttl = int(current_app.config["SESSION_TTL_SECONDS"])
    old_hash = hash_token(current_session_raw)
    new_raw = secrets.token_urlsafe(32)
    new_hash = hash_token(new_raw)
    new_cred_ver = int(user["credentials_version"]) + 1
    new_pw_hash = generate_password_hash(new_password, method="scrypt:32768:8:1")

    cur = conn.cursor()
    try:
        # Rotate session token
        cur.execute(
            """
            UPDATE dbo.login_sessions SET token_hash=?
            WHERE token_hash=? AND user_id=? AND revoked_at IS NULL AND expires_at>?
            """,
            (new_hash, old_hash, user_id, now),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return ChangePasswordResult.SESSION_EXPIRED

        # Update password + cred version
        cur.execute(
            "UPDATE dbo.users SET password_hash=?, credentials_version=?, updated_at=? WHERE id=?",
            (new_pw_hash, new_cred_ver, now, user_id),
        )

        # Thu hồi tất cả phiên khác
        revoke_user_sessions(conn, user_id, except_hash=new_hash)

        # Cập nhật session mới
        cur.execute(
            "UPDATE dbo.login_sessions SET credentials_version=?, last_seen_at=?, expires_at=? WHERE token_hash=?",
            (new_cred_ver, now, now + ttl, new_hash),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    from flask import session as flask_session
    flask_session["auth_token"] = new_raw
    flask_session.permanent = True
    return ChangePasswordResult.SUCCESS


# ── Reset password via email (S1-03) ──────────────────────────────────────────

def request_password_reset(email: str) -> str:
    norm = email.strip().lower()
    conn = get_db()
    user = fetch_one(conn, "SELECT id, email FROM dbo.users WHERE LOWER(email)=LOWER(?)", (norm,))
    if user is None:
        return GENERIC_RESET_MSG  # Không tiết lộ email có tồn tại

    user_id = int(user["id"])
    now = int(time.time())
    ttl = int(current_app.config["RESET_TOKEN_TTL_SECONDS"])
    raw = secrets.token_urlsafe(32)
    th = hash_token(raw)
    expires = now + ttl

    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE dbo.password_reset_tokens SET used_at=? WHERE user_id=? AND used_at IS NULL",
            (now, user_id),
        )
        cur.execute(
            """
            INSERT INTO dbo.password_reset_tokens
                (user_id, token_hash, expires_at, used_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (user_id, th, expires, now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    base = str(current_app.config["FRONTEND_BASE_URL"]).rstrip("/")
    reset_url = f"{base}/reset-password/{raw}"
    current_app.config["MAILER"].send_password_reset(str(user["email"]), reset_url)
    return GENERIC_RESET_MSG


def inspect_reset_token(token: str) -> bool:
    now = int(time.time())
    row = fetch_one(
        get_db(),
        "SELECT id FROM dbo.password_reset_tokens WHERE token_hash=? AND used_at IS NULL AND expires_at>?",
        (hash_token(token), now),
    )
    return row is not None


def reset_password(token: str, new_password: str) -> ResetPasswordResult:
    err = password_rule_error(new_password)
    if err:
        return ResetPasswordResult.INVALID_LINK  # Caller validates first

    conn = get_db()
    now = int(time.time())
    th = hash_token(token)
    new_pw_hash = generate_password_hash(new_password, method="scrypt:32768:8:1")
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, user_id FROM dbo.password_reset_tokens WITH (UPDLOCK, ROWLOCK)
            WHERE token_hash=? AND used_at IS NULL AND expires_at>?
            """,
            (th, now),
        )
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            return ResetPasswordResult.INVALID_LINK

        token_id, user_id = int(row[0]), int(row[1])
        cur.execute(
            "UPDATE dbo.users SET password_hash=?, updated_at=? WHERE id=?",
            (new_pw_hash, now, user_id),
        )
        cur.execute(
            "UPDATE dbo.password_reset_tokens SET used_at=? WHERE id=? AND used_at IS NULL",
            (now, token_id),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return ResetPasswordResult.INVALID_LINK
        conn.commit()
    except pyodbc.Error:
        conn.rollback()
        raise
    return ResetPasswordResult.SUCCESS
