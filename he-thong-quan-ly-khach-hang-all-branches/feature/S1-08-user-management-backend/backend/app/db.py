import os
from collections.abc import Iterable
from typing import Any

import pyodbc
from flask import g


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_connection_string() -> str:
    explicit = os.environ.get("SQL_SERVER_CONNECTION_STRING", "").strip()
    if explicit:
        return explicit

    driver = os.environ.get(
        "SQL_SERVER_DRIVER", "ODBC Driver 18 for SQL Server"
    )
    host = os.environ.get("SQL_SERVER_HOST", "localhost")
    port = os.environ.get("SQL_SERVER_PORT", "1433")
    database = os.environ.get("SQL_SERVER_DATABASE", "crm_db")
    encrypt = os.environ.get("SQL_SERVER_ENCRYPT", "yes")
    trust_certificate = os.environ.get(
        "SQL_SERVER_TRUST_CERTIFICATE", "yes"
    )

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={host},{port}",
        f"DATABASE={database}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust_certificate}",
    ]

    if _env_bool("SQL_SERVER_TRUSTED_CONNECTION"):
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={os.environ.get('SQL_SERVER_USER', 'sa')}")
        parts.append(f"PWD={os.environ.get('SQL_SERVER_PASSWORD', '')}")

    return ";".join(parts) + ";"


def get_db() -> pyodbc.Connection:
    connection = g.get("db")
    if connection is None:
        connection = pyodbc.connect(
            build_connection_string(),
            autocommit=False,
            timeout=5,
        )
        g.db = connection
    return connection


def close_db(_error: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def fetch_one(
    connection: pyodbc.Connection,
    sql: str,
    params: Iterable[Any] = (),
) -> dict[str, Any] | None:
    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    row = cursor.fetchone()
    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row, strict=True))


def fetch_all(
    connection: pyodbc.Connection,
    sql: str,
    params: Iterable[Any] = (),
) -> list[dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
