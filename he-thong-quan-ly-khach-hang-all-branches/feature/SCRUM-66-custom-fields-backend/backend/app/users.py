"""
users.py — Quản lý tài khoản người dùng (S1-08)
CRUD: list, create (+ activation email), update, activate
"""
import hashlib
import math
import re
import secrets
import string
import time
from typing import Any

import pyodbc
from flask import current_app
from werkzeug.security import generate_password_hash

from app.db import fetch_all, fetch_one, get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.fullmatch(normalize_email(email)))


def _gen_temp_password(length: int = 12) -> str:
    alpha = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alpha) for _ in range(length))
        if any(c.isalpha() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── List users (S1-08) ────────────────────────────────────────────────────────

def list_users(q: str, group: str, role: str, status: str, page: int, per_page: int) -> dict[str, Any]:
    conn = get_db()
    filters = ["1=1"]
    params: list[Any] = []

    if q:
        like = f"%{q}%"
        filters.append("(full_name LIKE ? OR email LIKE ? OR group_name LIKE ?)")
        params.extend([like, like, like])
    if group:
        filters.append("group_name=?"); params.append(group)
    if role:
        filters.append("role_name=?"); params.append(role)
    if status:
        filters.append("status=?"); params.append(status)

    where = " AND ".join(filters)
    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.users WHERE {where}", params)
    total = int(count_row["total"] or 0) if count_row else 0
    total_pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), total_pages)
    offset = (page - 1) * per_page

    items = fetch_all(
        conn,
        f"""
        SELECT id, full_name, email, group_name, role_name, status, created_at, updated_at
        FROM dbo.users WHERE {where}
        ORDER BY id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        [*params, offset, per_page],
    )
    stats_row = fetch_one(
        conn,
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status=N'Đang hoạt động' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN status=N'Chờ kích hoạt' THEN 1 ELSE 0 END) AS pending,
            COUNT(DISTINCT role_name) AS roles
        FROM dbo.users
        """,
    ) or {"total": 0, "active": 0, "pending": 0, "roles": 0}

    return {
        "items": items,
        "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages},
        "stats": {
            "total": int(stats_row["total"] or 0),
            "active": int(stats_row["active"] or 0),
            "pending": int(stats_row["pending"] or 0),
            "roles": int(stats_row["roles"] or 0),
        },
    }


# ── Create user (S1-08) ───────────────────────────────────────────────────────

def create_user(full_name: str, email: str, group_name: str, role_name: str) -> dict[str, Any]:
    conn = get_db()
    norm = normalize_email(email)

    existing = fetch_one(conn, "SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?)", (norm,))
    if existing:
        raise ValueError("duplicate_email")

    tmp_pwd = _gen_temp_password()
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    now = int(time.time())
    expires = now + int(current_app.config["ACTIVATION_TOKEN_TTL_SECONDS"])

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO dbo.users (full_name, email, password_hash, role, group_name, role_name, status, is_active, created_at, updated_at)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, N'employee', ?, ?, N'Chờ kích hoạt', 1, ?, ?)
            """,
            full_name, norm,
            generate_password_hash(tmp_pwd, method="scrypt:32768:8:1"),
            group_name, role_name, now, now,
        )
        user_id = int(cur.fetchone()[0])
        cur.execute(
            """
            INSERT INTO dbo.account_activation_tokens (user_id, token_hash, expires_at, used_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (user_id, token_hash, expires, now),
        )
        conn.commit()
    except pyodbc.IntegrityError as e:
        conn.rollback()
        raise ValueError("duplicate_email") from e
    except Exception:
        conn.rollback()
        raise

    base = str(current_app.config["FRONTEND_BASE_URL"]).rstrip("/")
    activation_url = f"{base}/activate?token={raw_token}"
    current_app.config["MAILER"].send_activation(norm, full_name, tmp_pwd, activation_url)

    return {"id": user_id, "email": norm, "status": "Chờ kích hoạt"}


# ── Update user (S1-08) ───────────────────────────────────────────────────────

def update_user(user_id: int, full_name: str, email: str, group_name: str, role_name: str) -> None:
    conn = get_db()
    norm = normalize_email(email)
    dup = fetch_one(
        conn,
        "SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?) AND id<>?",
        (norm, user_id),
    )
    if dup:
        raise ValueError("duplicate_email")
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE dbo.users SET full_name=?, email=?, group_name=?, role_name=?, updated_at=? WHERE id=?",
            (full_name, norm, group_name, role_name, int(time.time()), user_id),
        )
        if cur.rowcount != 1:
            conn.rollback()
            raise LookupError("user_not_found")
        conn.commit()
    except pyodbc.IntegrityError as e:
        conn.rollback()
        raise ValueError("duplicate_email") from e
    except Exception:
        conn.rollback()
        raise


# ── Activate account (S1-08) ─────────────────────────────────────────────────

def activate_account(raw_token: str) -> bool:
    conn = get_db()
    now = int(time.time())
    th = _hash_token(raw_token)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, user_id FROM dbo.account_activation_tokens WITH (UPDLOCK, ROWLOCK)
            WHERE token_hash=? AND used_at IS NULL AND expires_at>?
            """,
            (th, now),
        )
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            return False
        token_id, user_id = int(row[0]), int(row[1])
        cur.execute(
            "UPDATE dbo.users SET status=N'Đang hoạt động', updated_at=? WHERE id=?",
            (now, user_id),
        )
        cur.execute(
            "UPDATE dbo.account_activation_tokens SET used_at=? WHERE id=? AND used_at IS NULL",
            (now, token_id),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return False
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
