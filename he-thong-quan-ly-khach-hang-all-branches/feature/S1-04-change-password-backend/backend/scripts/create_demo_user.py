import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from app.db import build_connection_string  # noqa: E402
import pyodbc  # noqa: E402


def main() -> None:
    email = os.environ.get("DEMO_USER_EMAIL", "demo@company.local").strip().lower()
    password = os.environ.get("DEMO_USER_PASSWORD", "Demo@123456")
    now = int(time.time())

    connection = pyodbc.connect(build_connection_string(), autocommit=False, timeout=5)
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id FROM dbo.users WHERE LOWER(email) = LOWER(?)", email)
        if cursor.fetchone() is not None:
            print(f"Tài khoản {email} đã tồn tại.")
            return

        password_hash = generate_password_hash(password, method="scrypt:32768:8:1")
        cursor.execute(
            """
            INSERT INTO dbo.users (
                email, password_hash, credentials_version, created_at, updated_at
            )
            VALUES (?, ?, 1, ?, ?)
            """,
            email,
            password_hash,
            now,
            now,
        )
        connection.commit()
        print(f"Đã tạo tài khoản demo: {email}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
