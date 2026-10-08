import os
import re
from contextlib import contextmanager
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "CRM_SPRINT1")
DB_TRUSTED = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() in {"yes", "true", "1"}
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_ENCRYPT = os.getenv("DB_ENCRYPT", "no")


def _conn_string(database: str) -> str:
    parts = [
        f"DRIVER={{{DB_DRIVER}}}",
        f"SERVER={DB_SERVER}",
        f"DATABASE={database}",
        f"Encrypt={DB_ENCRYPT}",
        "TrustServerCertificate=yes",
    ]
    if DB_TRUSTED:
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend([f"UID={DB_USER}", f"PWD={DB_PASSWORD}"])
    return ";".join(parts) + ";"


def connect(database: str | None = None, autocommit: bool = False):
    return pyodbc.connect(_conn_string(database or DB_NAME), autocommit=autocommit)


@contextmanager
def db_cursor(commit: bool = False):
    conn = connect()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rows_to_dicts(cursor, rows):
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def row_to_dict(cursor, row):
    if row is None:
        return None
    columns = [c[0] for c in cursor.description]
    return dict(zip(columns, row))


def init_database():
    # Tạo database nếu chưa có rồi chạy schema idempotent.
    master = connect("master", autocommit=True)
    try:
        safe_name = DB_NAME.replace("]", "]]" )
        master.cursor().execute(
            f"IF DB_ID(?) IS NULL EXEC('CREATE DATABASE [{safe_name}]')", DB_NAME
        )
    finally:
        master.close()

    schema = (BASE_DIR / "database" / "schema.sql").read_text(encoding="utf-8")
    batches = [b.strip() for b in re.split(r"^\s*GO\s*$", schema, flags=re.I | re.M) if b.strip()]
    conn = connect(autocommit=True)
    try:
        cur = conn.cursor()
        for batch in batches:
            cur.execute(batch)
    finally:
        conn.close()
