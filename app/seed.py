from datetime import datetime

from .db import db_cursor
from .security import hash_password


def seed_demo_data():
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) FROM roles")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO roles(code,name) VALUES(?,?)",
                [
                    ("ADMIN", "Quản trị hệ thống"),
                    ("DIRECTOR", "Giám đốc kinh doanh"),
                    ("TEAM_LEADER", "Trưởng nhóm"),
                    ("SALES", "Nhân viên kinh doanh"),
                    ("REPORT_VIEWER", "Xem báo cáo"),
                ],
            )
        cur.execute("SELECT COUNT(*) FROM business_groups")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO business_groups(name) VALUES(?)",
                [("Nhóm Kinh doanh 1",), ("Nhóm Kinh doanh 2",)],
            )

        demo_users = [
            ("Quản trị viên", "admin@crm.local", "Admin@123", "active", "all", None, ["ADMIN"]),
            ("Giám đốc kinh doanh", "director@crm.local", "Director@123", "active", "all", None, ["DIRECTOR", "REPORT_VIEWER"]),
            ("Trưởng nhóm 1", "leader@crm.local", "Leader@123", "active", "group", 1, ["TEAM_LEADER", "SALES"]),
            ("Nhân viên 1", "sales1@crm.local", "Sales1@123", "active", "self", 1, ["SALES"]),
            ("Nhân viên 2", "sales2@crm.local", "Sales2@123", "active", "self", 1, ["SALES"]),
        ]
        for full_name, email, password, status, scope, group_id, roles in demo_users:
            cur.execute("SELECT id FROM users WHERE email=?", email)
            row = cur.fetchone()
            if row:
                user_id = row[0]
            else:
                cur.execute(
                    """INSERT INTO users(full_name,email,password_hash,status,data_scope,business_group_id,is_active,credentials_version,created_at,updated_at)
                       OUTPUT INSERTED.id VALUES(?,?,?,?,?,?,1,1,SYSUTCDATETIME(),SYSUTCDATETIME())""",
                    full_name, email, hash_password(password), status, scope, group_id,
                )
                user_id = cur.fetchone()[0]
            for code in roles:
                cur.execute("SELECT id FROM roles WHERE code=?", code)
                role_id = cur.fetchone()[0]
                cur.execute("IF NOT EXISTS(SELECT 1 FROM user_roles WHERE user_id=? AND role_id=?) INSERT INTO user_roles(user_id,role_id) VALUES(?,?)", user_id, role_id, user_id, role_id)

        cur.execute("SELECT COUNT(*) FROM customers")
        if cur.fetchone()[0] == 0:
            customers = [
                ("Công ty Sao Việt", "0901000001", "saoviet@example.com", 4, 1),
                ("Công ty Minh Anh", "0901000002", "minhanh@example.com", 4, 1),
                ("Cửa hàng An Phát", "0901000003", "anphat@example.com", 5, 1),
                ("Công ty Bắc Nam", "0901000004", "bacnam@example.com", 5, 1),
            ]
            cur.executemany("INSERT INTO customers(name,phone,email,owner_id,business_group_id,created_at) VALUES(?,?,?,?,?,SYSUTCDATETIME())", customers)
        cur.execute("SELECT COUNT(*) FROM opportunities")
        if cur.fetchone()[0] == 0:
            opps = [
                ("Gói CRM 2026 - Sao Việt", 120000000, "Đang tư vấn", 4, 1),
                ("Gia hạn CRM - Minh Anh", 45000000, "Báo giá", 4, 1),
                ("CRM cửa hàng - An Phát", 70000000, "Mới", 5, 1),
            ]
            cur.executemany("INSERT INTO opportunities(title,value,stage,owner_id,business_group_id,created_at) VALUES(?,?,?,?,?,SYSUTCDATETIME())", opps)
        cur.execute("SELECT COUNT(*) FROM activities")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO activities(subject,activity_type,owner_id,business_group_id) VALUES(?,?,?,?)", [("Gọi khách Sao Việt","Cuộc gọi",4,1),("Hẹn demo An Phát","Cuộc hẹn",5,1),("Gửi proposal Minh Anh","Email",4,1)])
        cur.execute("SELECT COUNT(*) FROM quotations")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO quotations(quote_no,total_amount,status,owner_id,business_group_id) VALUES(?,?,?,?,?)", [("BG-2026-001",120000000,"Đã gửi",4,1),("BG-2026-002",70000000,"Nháp",5,1)])
