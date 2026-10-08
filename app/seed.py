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

        # Dữ liệu mẫu Sprint 2/3
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO products(code,name,product_type,unit,list_price,floor_price,is_active) VALUES(?,?,?,?,?,?,1)",[
                ("CRM-BASIC","CRM Basic","Dịch vụ thuê bao","tháng",3000000,2500000),
                ("CRM-PRO","CRM Pro","Dịch vụ thuê bao","tháng",7000000,6000000),
                ("SETUP","Phí triển khai","Sản phẩm một lần","gói",15000000,12000000),
            ])
        cur.execute("SELECT COUNT(*) FROM sales_categories")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO sales_categories(category_type,value,sort_order,is_active) VALUES(?,?,?,1)",[
                ("Ngành nghề","Công nghệ",1),("Ngành nghề","Bán lẻ",2),("Quy mô","1-50",1),("Quy mô","51-200",2),("Nguồn lead","Website",1),("Loại hoạt động","Cuộc gọi",1)
            ])
        cur.execute("SELECT COUNT(*) FROM pipeline_stages")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO pipeline_stages(name,sort_order,win_probability,exit_condition,is_active) VALUES(?,?,?,?,1)",[
                ("Tiếp cận",1,10,"Đã liên hệ khách hàng"),("Xác định nhu cầu",2,25,"Có ghi chú nhu cầu"),("Đề xuất giải pháp",3,45,"Đã gửi đề xuất"),("Báo giá",4,65,"Có báo giá"),("Đàm phán",5,80,"Đã xác nhận điều khoản"),("Chốt",6,100,"Đã ký hoặc xác định kết quả")
            ])
        cur.execute("SELECT COUNT(*) FROM win_loss_reasons")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO win_loss_reasons(result_type,reason,sort_order,is_active) VALUES(?,?,?,1)",[
                ("Thắng","Giá phù hợp",1),("Thắng","Tính năng đáp ứng tốt",2),("Thua","Giá cao",1),("Thua","Chọn đối thủ",2)
            ])
        # Không tự động sửa dữ liệu Sprint 1.
        # Sprint 2/3 chỉ mở rộng schema và thêm dữ liệu ở các bảng mới.
        # Các hồ sơ khách hàng/cơ hội/hoạt động đã có từ Sprint 1 được giữ nguyên.

        # Tạo một khách hàng demo RIÊNG cho Sprint 3 nếu chưa có, thay vì cập nhật
        # các khách hàng Sprint 1. Điều này giúp demo các module mới mà không làm
        # thay đổi dữ liệu cũ.
        cur.execute("SELECT id FROM customers WHERE email=?", "sprint3.demo@crm.local")
        demo_customer = cur.fetchone()
        if demo_customer:
            demo_customer_id = demo_customer[0]
        else:
            cur.execute("SELECT id,business_group_id FROM users WHERE email=?", "sales1@crm.local")
            owner = cur.fetchone()
            if owner:
                cur.execute(
                    """INSERT INTO customers(name,phone,email,owner_id,business_group_id,created_at,tax_code,industry,company_size,website,address,status,last_interaction_at)
                       OUTPUT INSERTED.id VALUES(?,?,?,?,?,SYSUTCDATETIME(),?,?,?,?,?,?,DATEADD(day,-45,SYSUTCDATETIME()))""",
                    "Công ty Demo Sprint 3", "0901999999", "sprint3.demo@crm.local", owner[0], owner[1],
                    "0101999999", "Công nghệ", "51-200", "https://sprint3-demo.local", "Thái Nguyên", "Tiềm năng",
                )
                demo_customer_id = cur.fetchone()[0]
            else:
                demo_customer_id = None

        if demo_customer_id:
            cur.execute("SELECT COUNT(*) FROM contacts WHERE customer_id=?", demo_customer_id)
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO contacts(customer_id,full_name,title,email,phone,buying_role,is_primary) VALUES(?,?,?,?,?,?,?)",
                    [
                        (demo_customer_id,"Nguyễn Minh Demo","Giám đốc","minh.demo@sprint3.local","0911111111","Người quyết định",1),
                        (demo_customer_id,"Lê Hoa Demo","Kế toán","hoa.demo@sprint3.local","0922222222","Người ảnh hưởng",0),
                    ],
                )
            cur.execute("SELECT COUNT(*) FROM support_tickets WHERE customer_id=?", demo_customer_id)
            if cur.fetchone()[0] == 0:
                cur.execute("SELECT id FROM users WHERE email=?", "sales1@crm.local")
                assignee = cur.fetchone()
                assignee_id = assignee[0] if assignee else None
                cur.executemany(
                    "INSERT INTO support_tickets(customer_id,title,priority,status,assignee_id) VALUES(?,?,?,N'Mở',?)",
                    [
                        (demo_customer_id,"Yêu cầu hỗ trợ demo 1","Cao",assignee_id),
                        (demo_customer_id,"Yêu cầu hỗ trợ demo 2","Trung bình",assignee_id),
                        (demo_customer_id,"Yêu cầu hỗ trợ demo 3","Cao",assignee_id),
                    ],
                )

