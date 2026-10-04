import os
from contextlib import contextmanager

import pyodbc
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_connection_string() -> str:
    explicit = os.getenv("SQL_SERVER_CONNECTION_STRING", "").strip()
    if explicit:
        return explicit

    driver = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    host = os.getenv("SQL_SERVER_HOST", "localhost")
    port = os.getenv("SQL_SERVER_PORT", "1433")
    database = os.getenv("SQL_SERVER_DATABASE", "crm_db")
    encrypt = os.getenv("SQL_SERVER_ENCRYPT", "yes")
    trust = os.getenv("SQL_SERVER_TRUST_CERTIFICATE", "yes")

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={host},{port}",
        f"DATABASE={database}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust}",
    ]

    if _env_bool("SQL_SERVER_TRUSTED_CONNECTION"):
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={os.getenv('SQL_SERVER_USER', 'sa')}")
        parts.append(f"PWD={os.getenv('SQL_SERVER_PASSWORD', '')}")

    return ";".join(parts) + ";"


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(
        build_connection_string(),
        autocommit=False,
        timeout=5,
    )


def row_to_dict(cursor, row):
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row, strict=True))


def fetch_one(cursor, sql: str, params=()):
    cursor.execute(sql, tuple(params))
    return row_to_dict(cursor, cursor.fetchone())


@contextmanager
def transaction():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
