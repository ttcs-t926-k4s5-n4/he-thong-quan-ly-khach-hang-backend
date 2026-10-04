"""
seed_data.py — Khởi tạo dữ liệu mẫu toàn diện cho Sprint 1 & SCRUM-66:
- Tài khoản người dùng mẫu
- Định nghĩa Trường tùy chỉnh mẫu cho Khách hàng & Cơ hội (văn bản, số, ngày, danh sách chọn)
- Dữ liệu Khách hàng & Cơ hội kèm giá trị trường tùy chỉnh
"""
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

CUSTOM_FIELD_DEFS = [
    # Customer custom fields
    {
        "entity_type": "customer",
        "field_key": "industry",
        "field_label": "Ngành nghề kinh doanh",
        "field_type": "select",
        "options": ["Công nghệ", "Tài chính - Ngân hàng", "Bất động sản", "Bán lẻ", "Sản xuất"],
        "is_required": True,
        "description": "Lĩnh vực hoạt động chính của đối tác",
        "display_order": 10,
    },
    {
        "entity_type": "customer",
        "field_key": "tax_code",
        "field_label": "Mã số thuế",
        "field_type": "text",
        "options": None,
        "is_required": False,
        "description": "Mã số thuế doanh nghiệp (nếu có)",
        "display_order": 20,
    },
    {
        "entity_type": "customer",
        "field_key": "budget_usd",
        "field_label": "Ngân sách dự kiến (USD)",
        "field_type": "number",
        "options": None,
        "is_required": False,
        "description": "Khả năng chi trả tối đa của khách hàng",
        "display_order": 30,
    },
    {
        "entity_type": "customer",
        "field_key": "contract_sign_date",
        "field_label": "Ngày dự kiến ký hợp đồng",
        "field_type": "date",
        "options": None,
        "is_required": False,
        "description": "Hạn chót chốt hợp đồng (YYYY-MM-DD)",
        "display_order": 40,
    },
    # Opportunity custom fields
    {
        "entity_type": "opportunity",
        "field_key": "lead_source",
        "field_label": "Nguồn cơ hội",
        "field_type": "select",
        "options": ["Website", "Facebook", "Giới thiệu", "Hội thảo", "Cold Call"],
        "is_required": True,
        "description": "Kênh mang lại cơ hội này",
        "display_order": 10,
    },
    {
        "entity_type": "opportunity",
        "field_key": "margin_percent",
        "field_label": "Tỷ lệ lợi nhuận (%)",
        "field_type": "number",
        "options": None,
        "is_required": False,
        "description": "Tỷ suất lợi nhuận gộp ước tính",
        "display_order": 20,
    },
    {
        "entity_type": "opportunity",
        "field_key": "decision_maker",
        "field_label": "Người quyết định chính",
        "field_type": "text",
        "options": None,
        "is_required": False,
        "description": "Tên & Chức vụ người phê duyệt hợp đồng",
        "display_order": 30,
    },
]

SEED_CUSTOMERS = [
    {
        "name": "Công ty TNHH Giải pháp Công nghệ Alpha",
        "phone": "0901234567",
        "email": "contact@alpha-tech.vn",
        "address": "Tầng 5, Tòa nhà Landmark 81, Bình Thạnh, TP.HCM",
        "status": "Tiềm năng",
        "custom_fields": {
            "industry": "Công nghệ",
            "tax_code": "0109876543",
            "budget_usd": "25000",
            "contract_sign_date": "2026-11-15",
        },
    },
    {
        "name": "Tập đoàn Bất động sản Hòa Bình",
        "phone": "0912345678",
        "email": "info@hoabinh-real.vn",
        "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
        "status": "Đang chăm sóc",
        "custom_fields": {
            "industry": "Bất động sản",
            "tax_code": "0301122334",
            "budget_usd": "80000",
            "contract_sign_date": "2026-12-01",
        },
    },
]

SEED_OPPORTUNITIES = [
    {
        "title": "Hợp đồng triển khai Hệ thống CRM Cloud",
        "customer_idx": 0,
        "value": 500000000,
        "stage": "Đàm phán",
        "expected_close_date": "2026-11-30",
        "custom_fields": {
            "lead_source": "Website",
            "margin_percent": "35.5",
            "decision_maker": "Ông Nguyễn Văn A - CEO",
        },
    },
    {
        "title": "Tư vấn Quản trị Khách hàng Đa kênh",
        "customer_idx": 1,
        "value": 250000000,
        "stage": "Gửi báo giá",
        "expected_close_date": "2026-12-15",
        "custom_fields": {
            "lead_source": "Giới thiệu",
            "margin_percent": "40",
            "decision_maker": "Bà Trần Thị B - Giám đốc CNTT",
        },
    },
]


def main():
    print("--- Dang ket noi toi SQL Server ---")
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True, timeout=10)
    except Exception as e:
        print(f"Loi ket noi SQL Server: {e}")
        sys.exit(1)

    cur = conn.cursor()
    now = int(time.time() * 1000)

    # 1. Seed Users
    print("\n--- 1. Tao Tai khoan Mau ---")
    for full_name, email, password, role, group_name, role_name in SEED_USERS:
        cur.execute("SELECT id FROM dbo.users WHERE LOWER(email)=LOWER(?)", (email,))
        if cur.fetchone():
            print(f"  [Skip] [User] {email} da ton tai.")
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
        print(f"  [OK]   [User] {email} / {password} ({role})")

    # 2. Seed Custom Field Definitions
    print("\n--- 2. Tao Dinh nghia Truong tuy chinh (SCRUM-66) ---")
    cf_id_map = {}
    for cf in CUSTOM_FIELD_DEFS:
        cur.execute(
            "SELECT id FROM dbo.custom_field_definitions WHERE entity_type = ? AND field_key = ?",
            (cf["entity_type"], cf["field_key"]),
        )
        row = cur.fetchone()
        opts_json = json.dumps(cf["options"], ensure_ascii=False) if cf["options"] else None
        if row:
            cf_id_map[(cf["entity_type"], cf["field_key"])] = row[0]
            print(f"  [Skip] [Field] {cf['entity_type']}.{cf['field_key']} da ton tai.")
        else:
            cur.execute(
                """
                INSERT INTO dbo.custom_field_definitions
                (entity_type, field_key, field_label, field_type, options, is_required, description, display_order, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    cf["entity_type"],
                    cf["field_key"],
                    cf["field_label"],
                    cf["field_type"],
                    opts_json,
                    1 if cf["is_required"] else 0,
                    cf["description"],
                    cf["display_order"],
                    now,
                    now,
                ),
            )
            cur.execute("SELECT id FROM dbo.custom_field_definitions WHERE entity_type = ? AND field_key = ?", (cf["entity_type"], cf["field_key"]))
            new_id = cur.fetchone()[0]
            cf_id_map[(cf["entity_type"], cf["field_key"])] = new_id
            print(f"  [OK]   [Field] {cf['entity_type']}.{cf['field_key']} ({cf['field_type']}) - {cf['field_label']}")

    # 3. Seed Customers & Values
    print("\n--- 3. Tao Khach hang & Gia tri Truong tuy chinh ---")
    customer_ids = []
    for c in SEED_CUSTOMERS:
        cur.execute("SELECT id FROM dbo.customers WHERE name = ?", (c["name"],))
        row = cur.fetchone()
        if row:
            cid = row[0]
            print(f"  [Skip] [Customer] {c['name']} da ton tai.")
        else:
            cur.execute(
                """
                INSERT INTO dbo.customers (name, phone, email, address, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (c["name"], c["phone"], c["email"], c["address"], c["status"], now, now),
            )
            cur.execute("SELECT MAX(id) FROM dbo.customers")
            cid = cur.fetchone()[0]
            print(f"  [OK]   [Customer] {c['name']}")

        customer_ids.append(cid)
        for key, val in c["custom_fields"].items():
            fid = cf_id_map.get(("customer", key))
            if fid:
                cur.execute(
                    "SELECT id FROM dbo.custom_field_values WHERE entity_type = 'customer' AND entity_id = ? AND field_id = ?",
                    (cid, fid),
                )
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO dbo.custom_field_values (entity_type, entity_id, field_id, field_value, created_at, updated_at) VALUES ('customer', ?, ?, ?, ?, ?)",
                        (cid, fid, str(val), now, now),
                    )

    # 4. Seed Opportunities & Values
    print("\n--- 4. Tao Co hoi & Gia tri Truong tuy chinh ---")
    for o in SEED_OPPORTUNITIES:
        cur.execute("SELECT id FROM dbo.opportunities WHERE title = ?", (o["title"],))
        row = cur.fetchone()
        cid = customer_ids[o["customer_idx"]]
        if row:
            oid = row[0]
            print(f"  [Skip] [Opportunity] {o['title']} da ton tai.")
        else:
            cur.execute(
                """
                INSERT INTO dbo.opportunities (title, customer_id, value, stage, expected_close_date, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (o["title"], cid, float(o["value"]), o["stage"], o["expected_close_date"], now, now),
            )
            cur.execute("SELECT MAX(id) FROM dbo.opportunities")
            oid = cur.fetchone()[0]
            print(f"  [OK]   [Opportunity] {o['title']}")

        for key, val in o["custom_fields"].items():
            fid = cf_id_map.get(("opportunity", key))
            if fid:
                cur.execute(
                    "SELECT id FROM dbo.custom_field_values WHERE entity_type = 'opportunity' AND entity_id = ? AND field_id = ?",
                    (oid, fid),
                )
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO dbo.custom_field_values (entity_type, entity_id, field_id, field_value, created_at, updated_at) VALUES ('opportunity', ?, ?, ?, ?, ?)",
                        (oid, fid, str(val), now, now),
                    )

    conn.close()
    print("\nKhoi tao du lieu mau hoan tat!")

if __name__ == "__main__":
    main()

