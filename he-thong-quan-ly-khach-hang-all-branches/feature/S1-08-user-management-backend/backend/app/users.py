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

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(normalize_email(email)))


def generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(char.isalpha() for char in password) and any(
            char.isdigit() for char in password
        ):
            return password


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def activation_url(token: str) -> str:
    base = str(current_app.config["FRONTEND_BASE_URL"]).rstrip("/")
    return f"{base}/activate?token={token}"


def list_users(
    q: str,
    group_name: str,
    role_name: str,
    status: str,
    page: int,
    per_page: int,
) -> dict[str, Any]:
    connection = get_db()

    filters: list[str] = ["1 = 1"]
    params: list[Any] = []

    if q:
        like = f"%{q}%"
        filters.append(
            "(full_name LIKE ? OR email LIKE ? OR group_name LIKE ?)"
        )
        params.extend([like, like, like])

    if group_name:
        filters.append("group_name = ?")
        params.append(group_name)

    if role_name:
        filters.append("role_name = ?")
        params.append(role_name)

    if status:
        filters.append("status = ?")
        params.append(status)

    where = " AND ".join(filters)

    count_row = fetch_one(
        connection,
        f"SELECT COUNT(*) AS total FROM dbo.users WHERE {where}",
        params,
    )
    total = int(count_row["total"]) if count_row else 0
    total_pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), total_pages)
    offset = (page - 1) * per_page

    items = fetch_all(
        connection,
        f"""
        SELECT
            id,
            full_name,
            email,
            group_name,
            role_name,
            status,
            created_at,
            updated_at
        FROM dbo.users
        WHERE {where}
        ORDER BY id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        [*params, offset, per_page],
    )

    stats = fetch_one(
        connection,
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = N'Đang hoạt động' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN status = N'Chờ kích hoạt' THEN 1 ELSE 0 END) AS pending,
            COUNT(DISTINCT role_name) AS roles
        FROM dbo.users
        """,
    ) or {"total": 0, "active": 0, "pending": 0, "roles": 0}

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
        "stats": {
            "total": int(stats["total"] or 0),
            "active": int(stats["active"] or 0),
            "pending": int(stats["pending"] or 0),
            "roles": int(stats["roles"] or 0),
        },
    }


def create_user(
    full_name: str,
    email: str,
    group_name: str,
    role_name: str,
) -> dict[str, Any]:
    connection = get_db()
    normalized_email = normalize_email(email)

    existing = fetch_one(
        connection,
        "SELECT id FROM dbo.users WHERE LOWER(email) = LOWER(?)",
        (normalized_email,),
    )
    if existing is not None:
        raise ValueError("duplicate_email")

    temporary_password = generate_temporary_password()
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    now = int(time.time())
    expires_at = now + int(current_app.config["ACTIVATION_TOKEN_TTL_SECONDS"])

    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO dbo.users (
                full_name,
                email,
                password_hash,
                group_name,
                role_name,
                status,
                created_at,
                updated_at
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, N'Chờ kích hoạt', ?, ?)
            """,
            full_name,
            normalized_email,
            generate_password_hash(
                temporary_password,
                method="scrypt:32768:8:1",
            ),
            group_name,
            role_name,
            now,
            now,
        )
        user_id = int(cursor.fetchone()[0])

        cursor.execute(
            """
            INSERT INTO dbo.account_activation_tokens (
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
    except pyodbc.IntegrityError as error:
        connection.rollback()
        raise ValueError("duplicate_email") from error
    except Exception:
        connection.rollback()
        raise

    # Gửi mật khẩu tạm chỉ qua email, không trả plaintext về frontend.
    current_app.config["MAILER"].send_activation(
        normalized_email,
        full_name,
        temporary_password,
        activation_url(raw_token),
    )

    return {
        "id": user_id,
        "email": normalized_email,
        "status": "Chờ kích hoạt",
    }


def update_user(
    user_id: int,
    full_name: str,
    email: str,
    group_name: str,
    role_name: str,
) -> None:
    connection = get_db()
    normalized_email = normalize_email(email)

    duplicate = fetch_one(
        connection,
        """
        SELECT id
        FROM dbo.users
        WHERE LOWER(email) = LOWER(?) AND id <> ?
        """,
        (normalized_email, user_id),
    )
    if duplicate is not None:
        raise ValueError("duplicate_email")

    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE dbo.users
            SET
                full_name = ?,
                email = ?,
                group_name = ?,
                role_name = ?,
                updated_at = ?
            WHERE id = ?
            """,
            full_name,
            normalized_email,
            group_name,
            role_name,
            int(time.time()),
            user_id,
        )
        if cursor.rowcount != 1:
            connection.rollback()
            raise LookupError("user_not_found")
        connection.commit()
    except pyodbc.IntegrityError as error:
        connection.rollback()
        raise ValueError("duplicate_email") from error
    except Exception:
        connection.rollback()
        raise


def activate_account(raw_token: str) -> bool:
    connection = get_db()
    now = int(time.time())
    token_hash = hash_token(raw_token)
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id, user_id
            FROM dbo.account_activation_tokens WITH (UPDLOCK, ROWLOCK)
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
            return False

        token_id = int(row[0])
        user_id = int(row[1])

        cursor.execute(
            """
            UPDATE dbo.users
            SET status = N'Đang hoạt động', updated_at = ?
            WHERE id = ?
            """,
            now,
            user_id,
        )

        cursor.execute(
            """
            UPDATE dbo.account_activation_tokens
            SET used_at = ?
            WHERE id = ? AND used_at IS NULL
            """,
            now,
            token_id,
        )

        if cursor.rowcount != 1:
            connection.rollback()
            return False

        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
