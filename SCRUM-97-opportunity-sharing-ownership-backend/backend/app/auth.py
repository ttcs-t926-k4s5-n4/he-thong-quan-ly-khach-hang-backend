"""
auth.py — Xác thực, session & khóa tài khoản
Covers: S1-01 (login), S1-02 (session), S1-10 (lock after 5 failures)
"""
import hashlib
import secrets
import time
from dataclasses import dataclass

import pyodbc
from flask import current_app, g, session
from werkzeug.security import check_password_hash

from app.db import fetch_one, get_db

GENERIC_LOGIN_MSG = "Email hoặc mật khẩu không đúng."
LOCKED_MSG = "Đăng nhập không thành công. Tài khoản bị khóa tạm 15 phút."
ROLE_LABEL = {
    "admin": "Quản trị hệ thống",
    "manager": "Giám đốc kinh doanh",
    "employee": "Nhân viên kinh doanh",
}
ROLE_HOME = {
    "admin": "/dashboard/admin",
    "manager": "/dashboard/manager",
    "employee": "/dashboard/employee",
}


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email: str
    full_name: str
    role: str
    credentials_version: int


# ── Helpers ──────────────────────────────────────────────────────────────────

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Login (S1-01 + S1-10) ────────────────────────────────────────────────────

def login(email: str, password: str) -> tuple[int, dict]:
    db = get_db()
    row = fetch_one(
        db,
        """
        SELECT id, full_name, email, password_hash, role,
               failed_login_attempts, locked_until, is_active,
               credentials_version
        FROM dbo.users
        WHERE LOWER(email) = LOWER(?)
        """,
        (email.strip().lower(),),
    )

    if row is None:
        return 401, {"message": GENERIC_LOGIN_MSG}

    if not row["is_active"]:
        return 401, {"message": "Tài khoản đã bị vô hiệu hóa."}

    now = int(time.time())
    failures = int(row["failed_login_attempts"] or 0)
    locked_until = row["locked_until"]
    user_id = int(row["id"])
    cur = db.cursor()

    # Kiểm tra khóa
    if locked_until is not None and int(locked_until) > now:
        return 429, {"message": LOCKED_MSG}

    # Hết hạn khóa → reset
    if locked_until is not None and int(locked_until) <= now:
        cur.execute(
            "UPDATE dbo.users SET failed_login_attempts=0, locked_until=NULL WHERE id=?",
            (user_id,),
        )
        db.commit()
        failures = 0

    # Sai mật khẩu
    if not check_password_hash(str(row["password_hash"]), password):
        failures += 1
        max_fail = int(current_app.config["LOGIN_MAX_FAILURES"])
        lock_until = now + int(current_app.config["LOGIN_LOCK_SECONDS"]) if failures >= max_fail else None
        cur.execute(
            "UPDATE dbo.users SET failed_login_attempts=?, locked_until=? WHERE id=?",
            (failures, lock_until, user_id),
        )
        db.commit()
        if lock_until:
            return 429, {"message": LOCKED_MSG}
        remaining = max_fail - failures
        return 401, {
            "message": GENERIC_LOGIN_MSG,
            "attempts_remaining": remaining,
        }

    # Đúng → reset failures, tạo session
    cur.execute(
        "UPDATE dbo.users SET failed_login_attempts=0, locked_until=NULL WHERE id=?",
        (user_id,),
    )
    db.commit()

    raw_token = secrets.token_urlsafe(32)
    token_h = hash_token(raw_token)
    ttl = int(current_app.config["SESSION_TTL_SECONDS"])
    expires = now + ttl
    cred_ver = int(row["credentials_version"])

    # Thu hồi session cũ (nếu có)
    old_raw = session.get("auth_token")
    if old_raw:
        cur.execute(
            "UPDATE dbo.login_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
            (now, hash_token(old_raw)),
        )

    cur.execute(
        """
        INSERT INTO dbo.login_sessions
            (token_hash, user_id, credentials_version, created_at, last_seen_at, expires_at, revoked_at)
        VALUES (?, ?, ?, ?, ?, ?, NULL)
        """,
        (token_h, user_id, cred_ver, now, now, expires),
    )
    db.commit()

    session.clear()
    session["auth_token"] = raw_token
    session.permanent = True

    role = str(row["role"])
    return 200, {
        "message": "Đăng nhập thành công.",
        "user": {
            "id": user_id,
            "full_name": str(row["full_name"]),
            "email": str(row["email"]),
            "role": role,
            "role_label": ROLE_LABEL.get(role, role),
        },
        "redirect_url": ROLE_HOME.get(role, "/dashboard/employee"),
    }


# ── Session management (S1-02) ───────────────────────────────────────────────

def get_current_user() -> CurrentUser | None:
    return g.get("current_user")


def load_current_user() -> None:
    g.current_user = None
    raw = session.get("auth_token")
    if not isinstance(raw, str) or not raw:
        return
    now = int(time.time())
    db = get_db()
    row = fetch_one(
        db,
        """
        SELECT u.id, u.email, u.full_name, u.role, u.credentials_version, s.last_seen_at
        FROM dbo.login_sessions AS s
        JOIN dbo.users AS u ON u.id = s.user_id
        WHERE s.token_hash = ?
          AND s.revoked_at IS NULL
          AND s.expires_at > ?
          AND s.credentials_version = u.credentials_version
          AND u.is_active = 1
        """,
        (hash_token(raw), now),
    )
    if row is None:
        session.pop("auth_token", None)
        return
    g.current_user = CurrentUser(
        id=int(row["id"]),
        email=str(row["email"]),
        full_name=str(row["full_name"]),
        role=str(row["role"]),
        credentials_version=int(row["credentials_version"]),
    )
    # Sliding window renew
    if now - int(row["last_seen_at"]) >= 60:
        ttl = int(current_app.config["SESSION_TTL_SECONDS"])
        cur = db.cursor()
        cur.execute(
            "UPDATE dbo.login_sessions SET last_seen_at=?, expires_at=? WHERE token_hash=?",
            (now, now + ttl, hash_token(raw)),
        )
        db.commit()


def logout_current_user() -> None:
    raw = session.get("auth_token")
    if raw:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE dbo.login_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
            (int(time.time()), hash_token(raw)),
        )
        db.commit()
    session.pop("auth_token", None)


def revoke_user_sessions(conn: pyodbc.Connection, user_id: int, except_hash: str | None = None) -> None:
    now = int(time.time())
    cur = conn.cursor()
    if except_hash:
        cur.execute(
            "UPDATE dbo.login_sessions SET revoked_at=? WHERE user_id=? AND token_hash<>? AND revoked_at IS NULL",
            (now, user_id, except_hash),
        )
    else:
        cur.execute(
            "UPDATE dbo.login_sessions SET revoked_at=? WHERE user_id=? AND revoked_at IS NULL",
            (now, user_id),
        )
