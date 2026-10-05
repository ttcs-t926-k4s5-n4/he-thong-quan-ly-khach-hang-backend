"""Script tạo dữ liệu mẫu với hash mật khẩu đúng. Chạy một lần sau khi tạo DB."""
import os
import sys
import time
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

import pyodbc
from werkzeug.security import generate_password_hash

CONN_STR = (
    f"DRIVER={{{os.environ.get('SQL_SERVER_DRIVER','ODBC Driver 18 for SQL Server')}}};"
    f"SERVER={os.environ.get('SQL_SERVER_HOST','localhost')},{os.environ.get('SQL_SERVER_PORT','1433')};"
    f"DATABASE={os.environ.get('SQL_SERVER_DATABASE','crm_db')};"
    f"UID={os.environ.get('SQL_SERVER_USER','sa')};"
    f"PWD={os.environ.get('SQL_SERVER_PASSWORD','')};"
    f"Encrypt={os.environ.get('SQL_SERVER_ENCRYPT','yes')};"
    f"TrustServerCertificate={os.environ.get('SQL_SERVER_TRUST_CERTIFICATE','yes')};"
)

SEED_USERS = [
    ("Quản trị viên", "admin@company.vn", "Admin@123", "admin", "Quản trị", "Quản trị hệ thống"),
    ("Giám đốc Kinh doanh", "manager@company.vn", "Manager@123", "manager", "Kinh doanh", "Giám đốc kinh doanh"),
    ("Nhân viên Kinh doanh", "employee@company.vn", "Employee@123", "employee", "Kinh doanh", "Nhân viên kinh doanh"),
]

def main():
    print("Kết nối SQL Server...")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True, timeout=10)
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        sys.exit(1)

    cur = conn.cursor()
    now = int(time.time())
    created = 0
    for full_name, email, password, role, group_name, role_name in SEED_USERS:
        cur.execute("SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?)", (email,))
        if cur.fetchone():
            print(f"  ⏭  {email} đã tồn tại, bỏ qua.")
            continue
        pw_hash = generate_password_hash(password, method="scrypt:32768:8:1")
        cur.execute(
            """
            INSERT INTO dbo.users
                (full_name, email, password_hash, role, group_name, role_name, status, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, N'Đang hoạt động', 1, ?, ?)
            """,
            (full_name, email, pw_hash, role, group_name, role_name, now, now),
        )
        print(f"  ✓  Tạo {email} / {password}")
        created += 1

    conn.close()
    print(f"\nHoàn tất. Đã tạo {created} tài khoản.")
    print("\nTài khoản mẫu:")
    for _, email, password, role, _, _ in SEED_USERS:
        print(f"  {role:10s}  {email}  /  {password}")

if __name__ == "__main__":
    main()
