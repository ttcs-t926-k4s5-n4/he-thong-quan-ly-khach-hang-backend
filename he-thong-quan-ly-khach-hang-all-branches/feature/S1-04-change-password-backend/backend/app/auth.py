import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Any

import pyodbc
from flask import current_app, g, session

from app.db import fetch_one, get_db


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email: str
    credentials_version: int


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_current_user() -> CurrentUser | None:
    value = g.get("current_user")
    return value if isinstance(value, CurrentUser) else None


def load_current_user() -> None:
    g.current_user = None
    raw_token = session.get("auth_token")
    if not isinstance(raw_token, str) or not raw_token:
        return

    now = int(time.time())
    connection = get_db()
    row = fetch_one(
        connection,
        """
        SELECT
            u.id,
            u.email,
            u.credentials_version,
            s.last_seen_at
        FROM dbo.login_sessions AS s
        INNER JOIN dbo.users AS u ON u.id = s.user_id
        WHERE s.token_hash = ?
          AND s.revoked_at IS NULL
          AND s.expires_at > ?
          AND s.credentials_version = u.credentials_version
        """,
        (hash_session_token(raw_token), now),
    )

    if row is None:
        session.pop("auth_token", None)
        return

    g.current_user = CurrentUser(
        id=int(row["id"]),
        email=str(row["email"]),
        credentials_version=int(row["credentials_version"]),
    )

    if now - int(row["last_seen_at"]) >= 60:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE dbo.login_sessions SET last_seen_at = ? WHERE token_hash = ?",
            now,
            hash_session_token(raw_token),
        )
        connection.commit()


def login_user(user_id: int) -> bool:
    connection = get_db()
    user = fetch_one(
        connection,
        "SELECT id, credentials_version FROM dbo.users WHERE id = ?",
        (user_id,),
    )
    if user is None:
        return False

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_session_token(raw_token)
    previous_token = session.get("auth_token")
    previous_hash = (
        hash_session_token(previous_token)
        if isinstance(previous_token, str) and previous_token
        else None
    )

    now = int(time.time())
    expires_at = now + int(current_app.config["LOGIN_SESSION_TTL_SECONDS"])
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO dbo.login_sessions (
                token_hash,
                user_id,
                credentials_version,
                created_at,
                last_seen_at,
                expires_at,
                revoked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            token_hash,
            int(user["id"]),
            int(user["credentials_version"]),
            now,
            now,
            expires_at,
        )

        if previous_hash:
            cursor.execute(
                """
                UPDATE dbo.login_sessions
                SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                now,
                previous_hash,
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    session.clear()
    session["auth_token"] = raw_token
    session.permanent = True
    return True


def logout_current_user() -> None:
    raw_token = session.get("auth_token")
    if isinstance(raw_token, str) and raw_token:
        connection = get_db()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.login_sessions
                SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                int(time.time()),
                hash_session_token(raw_token),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    session.pop("auth_token", None)


def revoke_user_sessions(
    connection: pyodbc.Connection,
    user_id: int,
    except_token_hash: str | None = None,
) -> None:
    cursor = connection.cursor()
    now = int(time.time())

    if except_token_hash is None:
        cursor.execute(
            """
            UPDATE dbo.login_sessions
            SET revoked_at = ?
            WHERE user_id = ? AND revoked_at IS NULL
            """,
            now,
            user_id,
        )
        return

    cursor.execute(
        """
        UPDATE dbo.login_sessions
        SET revoked_at = ?
        WHERE user_id = ? AND token_hash <> ? AND revoked_at IS NULL
        """,
        now,
        user_id,
        except_token_hash,
    )
