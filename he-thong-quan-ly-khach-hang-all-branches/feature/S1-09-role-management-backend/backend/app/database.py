import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_connection_url() -> str:
    explicit = os.getenv("SQL_SERVER_CONNECTION_STRING", "").strip()
    if explicit:
        return explicit

    driver = os.getenv("SQL_SERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    host = os.getenv("SQL_SERVER_HOST", "localhost")
    port = os.getenv("SQL_SERVER_PORT", "1433")
    database = os.getenv("SQL_SERVER_DATABASE", "crm_db")
    encrypt = os.getenv("SQL_SERVER_ENCRYPT", "yes")
    trust = os.getenv("SQL_SERVER_TRUST_CERTIFICATE", "yes")

    if _env_bool("SQL_SERVER_TRUSTED_CONNECTION"):
        odbc = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust};"
        )
    else:
        user = os.getenv("SQL_SERVER_USER", "sa")
        password = os.getenv("SQL_SERVER_PASSWORD", "")
        odbc = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust};"
        )

    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


class Base(DeclarativeBase):
    pass


engine = create_engine(build_connection_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
