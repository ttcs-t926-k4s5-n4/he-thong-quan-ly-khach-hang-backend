import os
import pyodbc
from flask import g


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


def build_connection_string() -> str:
    explicit = os.environ.get("SQL_SERVER_CONNECTION_STRING", "").strip()
    if explicit:
        return explicit
    parts = [
        f"DRIVER={{{os.environ.get('SQL_SERVER_DRIVER','ODBC Driver 18 for SQL Server')}}}",
        f"SERVER={os.environ.get('SQL_SERVER_HOST','localhost')},{os.environ.get('SQL_SERVER_PORT','1433')}",
        f"DATABASE={os.environ.get('SQL_SERVER_DATABASE','crm_db')}",
        f"Encrypt={os.environ.get('SQL_SERVER_ENCRYPT','yes')}",
        f"TrustServerCertificate={os.environ.get('SQL_SERVER_TRUST_CERTIFICATE','yes')}",
    ]
    if _env_bool("SQL_SERVER_TRUSTED_CONNECTION"):
        parts.append("Trusted_Connection=yes")
    else:
        parts += [
            f"UID={os.environ.get('SQL_SERVER_USER','sa')}",
            f"PWD={os.environ.get('SQL_SERVER_PASSWORD','')}",
        ]
    return ";".join(parts) + ";"


def get_db() -> pyodbc.Connection:
    if "db" not in g:
        g.db = pyodbc.connect(build_connection_string(), autocommit=False, timeout=5)
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_one(conn, sql: str, params=()):
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    row = cur.fetchone()
    if row is None:
        return None
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))


def fetch_all(conn, sql: str, params=()):
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
