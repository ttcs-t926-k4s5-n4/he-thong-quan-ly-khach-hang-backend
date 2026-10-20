"""Tạo dữ liệu mẫu cho CRM.

Chạy từ thư mục dự án:
    python -m app.seed            # tạo dữ liệu nếu CSDL còn trống
    python -m app.seed --reset    # xoá toàn bộ dữ liệu cũ rồi tạo lại

Dữ liệu nghiệp vụ mẫu được tạo qua chính các service (đóng băng đồng hồ ở các mốc thời gian
trong quá khứ) nên luôn tuân thủ đúng quy tắc của 6 story.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import clock
from app.db import commit, drop_all, execute, init_db, scalar

DEMO_PASSWORD = "123456"
_HASHES: dict[str, str] = {}

STAGES = [
    # mã, tên, thứ tự, xác suất mặc định (%), ngưỡng đình trệ (ngày), thắng, thua
    ("prospecting", "Tiếp cận", 1, 10, 14, 0, 0),
    ("qualification", "Xác định nhu cầu", 2, 20, 14, 0, 0),
    ("proposal", "Đề xuất giải pháp", 3, 40, 21, 0, 0),
    ("quotation", "Báo giá", 4, 60, 14, 0, 0),
    ("negotiation", "Đàm phán", 5, 80, 10, 0, 0),
    ("won", "Thắng", 6, 100, None, 1, 0),
    ("lost", "Thua", 7, 0, None, 0, 1),
]

PRODUCTS = [
    # mã, tên, loại, đơn vị, chu kỳ thuê bao, giá niêm yết, mô tả
    ("CRM-STD", "Phần mềm CRM – Gói Tiêu chuẩn", "subscription", "người dùng", "month", 250_000,
     "Thuê bao theo tháng, tính theo số người dùng."),
    ("CRM-PRO", "Phần mềm CRM – Gói Chuyên nghiệp", "subscription", "người dùng", "month", 450_000,
     "Thuê bao theo tháng, đầy đủ tính năng tự động hoá và báo cáo."),
    ("HT-QUY", "Gói hỗ trợ kỹ thuật ưu tiên", "subscription", "gói", "quarter", 6_000_000,
     "Hỗ trợ 24/7, thanh toán theo quý."),
    ("MC-NAM", "Máy chủ lưu trữ đám mây", "subscription", "máy chủ", "year", 24_000_000,
     "Thuê máy chủ theo năm."),
    ("DV-TK", "Dịch vụ triển khai và cấu hình", "service", "gói", None, 15_000_000,
     "Triển khai, cấu hình và chuyển đổi dữ liệu (một lần)."),
    ("DV-DT", "Đào tạo người dùng", "service", "buổi", None, 3_000_000,
     "Đào tạo trực tiếp tại văn phòng khách hàng."),
    ("TB-MQ", "Máy quét mã vạch", "product", "cái", None, 2_500_000, "Máy quét mã vạch không dây."),
    ("TB-MIN", "Máy in hoá đơn nhiệt", "product", "cái", None, 1_800_000, "Máy in hoá đơn khổ 80 mm."),
    ("DV-TUYCHINH", "Tuỳ chỉnh tính năng theo yêu cầu", "service", "giờ", None, None,
     "Báo giá theo từng yêu cầu, chưa có giá niêm yết."),
]

TEAMS = ["Nhóm Kinh doanh Miền Bắc", "Nhóm Kinh doanh Miền Nam"]

USERS = [
    # tên đăng nhập, họ tên, email, vai trò, nhóm (chỉ số trong TEAMS)
    ("giamdoc", "Nguyễn Văn An", "an.nguyen@crm.local", "director", None),
    ("truongnhom1", "Trần Thị Bình", "binh.tran@crm.local", "team_lead", 0),
    ("nhanvien1", "Lê Văn Cường", "cuong.le@crm.local", "staff", 0),
    ("nhanvien2", "Phạm Thị Dung", "dung.pham@crm.local", "staff", 0),
    ("truongnhom2", "Hoàng Văn Em", "em.hoang@crm.local", "team_lead", 1),
    ("nhanvien3", "Vũ Thị Giang", "giang.vu@crm.local", "staff", 1),
    ("quantri", "Quản trị hệ thống", "admin@crm.local", "admin", None),
]

CUSTOMERS = [
    # khoá, tên, người phụ trách, điện thoại, email, người liên hệ (họ tên, chức danh)
    ("anh_duong", "Công ty CP Công nghệ Ánh Dương", "nhanvien1", "0241234567", "lienhe@anhduong.vn",
     [("Đỗ Minh Hải", "Giám đốc"), ("Ngô Thị Lan", "Trưởng phòng Mua hàng")]),
    ("hung_thinh", "Công ty TNHH Thương mại Hưng Thịnh", "nhanvien1", "0242345678", "info@hungthinh.vn",
     [("Bùi Văn Khoa", "Phó Giám đốc")]),
    ("an_khang", "Công ty CP Dược phẩm An Khang", "nhanvien2", "0243456789", "contact@ankhang.vn",
     [("Trịnh Thu Hà", "Kế toán trưởng"), ("Mai Quốc Tuấn", "Trưởng phòng CNTT")]),
    ("minh_tri", "Tập đoàn Giáo dục Minh Trí", "truongnhom1", "0244567890", "office@minhtri.edu.vn",
     [("Lý Thanh Tâm", "Giám đốc tài chính")]),
    ("sao_viet", "Công ty TNHH Logistics Sao Việt", "nhanvien3", "0285678901", "sales@saoviet.vn",
     [("Đặng Hoài Nam", "Giám đốc điều hành")]),
    ("phu_thanh", "Công ty CP Xây dựng Phú Thành", "nhanvien3", "0286789012", "hc@phuthanh.vn",
     [("Phan Văn Lộc", "Trưởng phòng Hành chính")]),
]


def password_hash(password: str = DEMO_PASSWORD) -> str:
    if password not in _HASHES:
        _HASHES[password] = generate_password_hash(password)
    return _HASHES[password]


def is_empty() -> bool:
    return (scalar("SELECT COUNT(*) FROM users") or 0) == 0


def seed_base() -> dict:
    """Danh mục và dữ liệu nền: giai đoạn, sản phẩm, bảng giá, nhóm, người dùng, khách hàng, người liên hệ."""
    now_text = clock.to_db(clock.now())
    ids: dict = {"stages": {}, "products": {}, "teams": [], "users": {}, "customers": {}, "contacts": {}}

    for code, name, order, probability, stale, won, lost in STAGES:
        ids["stages"][code] = execute(
            "INSERT INTO pipeline_stages (code, name, sort_order, default_probability, stale_after_days, "
            "is_won, is_lost) VALUES (?, ?, ?, ?, ?, ?, ?)", (code, name, order, probability, stale, won, lost))

    price_list_id = execute("INSERT INTO price_lists (name, is_default, valid_from, valid_to, is_active) "
                            "VALUES (?, 1, ?, NULL, 1)", ("Bảng giá niêm yết 2026", "2026-01-01"))
    for code, name, product_type, unit, period, price, description in PRODUCTS:
        product_id = execute(
            "INSERT INTO products (code, name, product_type, unit, billing_period, description) "
            "VALUES (?, ?, ?, ?, ?, ?)", (code, name, product_type, unit, period, description))
        ids["products"][code] = product_id
        if price is not None:
            execute("INSERT INTO price_list_items (price_list_id, product_id, unit_price) VALUES (?, ?, ?)",
                    (price_list_id, product_id, price))

    for team_name in TEAMS:
        ids["teams"].append(execute("INSERT INTO teams (name) VALUES (?)", (team_name,)))
    for username, full_name, email, role, team_index in USERS:
        team_id = ids["teams"][team_index] if team_index is not None else None
        ids["users"][username] = execute(
            "INSERT INTO users (username, full_name, email, password_hash, role, team_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", (username, full_name, email, password_hash(), role, team_id, now_text))
    execute("UPDATE teams SET leader_id = ? WHERE id = ?", (ids["users"]["truongnhom1"], ids["teams"][0]))
    execute("UPDATE teams SET leader_id = ? WHERE id = ?", (ids["users"]["truongnhom2"], ids["teams"][1]))

    for key, name, owner, phone, email, contacts in CUSTOMERS:
        customer_id = execute(
            "INSERT INTO customers (name, phone, email, owner_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, ids["users"][owner], now_text))
        ids["customers"][key] = customer_id
        for full_name, job_title in contacts:
            ids["contacts"][full_name] = execute(
                "INSERT INTO contacts (customer_id, full_name, job_title, created_at) VALUES (?, ?, ?, ?)",
                (customer_id, full_name, job_title, now_text))
    return ids


def seed_demo(ids: dict, base: datetime) -> None:
    """Luồng nghiệp vụ mẫu cho 6 story, tạo qua service với đồng hồ đóng băng ở các mốc quá khứ."""
    from app.auth import load_user
    from app.features.activities import service as activities
    from app.features.opportunities import service as opportunities
    from app.features.opportunity_lines import service as lines
    from app.features.stage_gates import service as gates
    from app.features.tasks import service as tasks

    user = {name: load_user(uid) for name, uid in ids["users"].items()}
    st, cu, ct, pr = ids["stages"], ids["customers"], ids["contacts"], ids["products"]
    cuong, dung, binh, giang = user["nhanvien1"], user["nhanvien2"], user["truongnhom1"], user["nhanvien3"]

    def at(days: int, hour: int = 9, minute: int = 0) -> None:
        moment = base.date() + timedelta(days=days)
        clock.freeze(datetime(moment.year, moment.month, moment.day, hour, minute))

    def day(days: int, time: str | None = None) -> str:
        text = (base.date() + timedelta(days=days)).isoformat()
        return f"{text}T{time}" if time else text

    def create(owner, days, **payload):
        at(days)
        return opportunities.create_opportunity(owner, payload)["opportunity"]["id"]

    def move(owner, opp_id, code, days, **extra):
        at(days, 10)
        gates.change_stage(owner, opp_id, {"to_stage_id": st[code], **extra})

    def add(owner, opp_id, days, **payload):
        at(days, 11)
        lines.add_line(owner, opp_id, payload)

    def log(owner, days, hour, **payload):
        at(days, hour)
        return activities.create_activity(owner, payload)["activity"]["id"]

    # SCRUM-90: Giám đốc cấu hình điều kiện bắt buộc khi rời giai đoạn
    at(-60)
    gates.create_rule(user["giamdoc"], {"stage_id": st["prospecting"], "rule_type": "required_field",
                                        "field_name": "primary_contact_id"})
    gates.create_rule(user["giamdoc"], {"stage_id": st["qualification"], "rule_type": "min_activities",
                                        "activity_type": "meeting", "min_count": 1})
    gates.create_rule(user["giamdoc"], {"stage_id": st["proposal"], "rule_type": "min_product_lines",
                                        "min_count": 1})

    # Cơ hội A – đi đủ các giai đoạn tới Báo giá rồi nằm yên 18 ngày (đình trệ)
    a = create(cuong, -30, name="Triển khai CRM cho 50 người dùng", customer_id=cu["anh_duong"],
               primary_contact_id=ct["Đỗ Minh Hải"], estimated_value=300_000_000, expected_close_date=day(20),
               source="referral", description="Chuẩn hoá quy trình bán hàng cho 3 chi nhánh.")
    log(cuong, -28, 14, activity_type="meeting", opportunity_id=a, contact_id=ct["Đỗ Minh Hải"],
        subject="Khảo sát quy trình bán hàng", content="Khảo sát quy trình bán hàng hiện tại tại văn phòng khách.",
        outcome="Khách đồng ý nhận đề xuất giải pháp.", occurred_at=day(-28, "09:30:00"), duration_minutes=90)
    move(cuong, a, "qualification", -27)
    move(cuong, a, "proposal", -25)
    add(cuong, a, -22, product_id=pr["CRM-PRO"], quantity=50, periods=12, discount_percent=5)
    add(cuong, a, -22, product_id=pr["DV-TK"], quantity=1)
    add(cuong, a, -22, product_id=pr["DV-DT"], quantity=4)
    move(cuong, a, "quotation", -18)
    log(cuong, -18, 15, activity_type="email", opportunity_id=a, contact_id=ct["Ngô Thị Lan"],
        subject="Gửi báo giá lần 1", content="Đã gửi báo giá chi tiết cho phòng mua hàng.")

    # Cơ hội B – cùng khách hàng Ánh Dương (nhiều cơ hội song song), ghi nhanh trên điện thoại
    b = create(cuong, -3, name="Mua máy quét mã vạch cho kho", customer_id=cu["anh_duong"],
               primary_contact_id=ct["Ngô Thị Lan"], estimated_value=25_000_000, expected_close_date=day(30),
               source="existing_customer")
    at(-1, 16, 30)
    activities.quick_log(cuong, {
        "activity_type": "meeting", "opportunity_id": b, "contact_id": ct["Ngô Thị Lan"],
        "content": "Khảo sát kho hàng, khách cần 6 máy quét và 2 máy in hoá đơn.",
        "outcome": "Khách muốn nhận báo giá trong tuần.", "duration_minutes": 45, "ended_minutes_ago": 10,
        "follow_up_task": {"title": "Gửi báo giá máy quét mã vạch", "due_date": day(2), "priority": "high"},
    })

    # Cơ hội C – quá ngày chốt, không có hoạt động (đình trệ)
    c = create(cuong, -20, name="Gói hỗ trợ kỹ thuật năm 2027", customer_id=cu["hung_thinh"],
               primary_contact_id=ct["Bùi Văn Khoa"], estimated_value=24_000_000, expected_close_date=day(-5),
               source="existing_customer")
    move(cuong, c, "qualification", -19)

    # Cơ hội D – nhóm Miền Bắc, thuê bao 24 tháng
    d = create(dung, -15, name="Số hoá quy trình bán hàng", customer_id=cu["an_khang"],
               primary_contact_id=ct["Mai Quốc Tuấn"], estimated_value=120_000_000, expected_close_date=day(45),
               source="website")
    log(dung, -14, 15, activity_type="meeting", opportunity_id=d, contact_id=ct["Mai Quốc Tuấn"],
        content="Trình bày giải pháp CRM cho ban giám đốc.", outcome="Khách yêu cầu demo trên dữ liệu thật.",
        occurred_at=day(-14, "10:00:00"), duration_minutes=60)
    move(dung, d, "qualification", -13)
    move(dung, d, "proposal", -12)
    add(dung, d, -10, product_id=pr["CRM-STD"], quantity=20, periods=24)
    add(dung, d, -10, product_id=pr["DV-TK"], quantity=1, unit_price=12_000_000,
        note="Giảm giá triển khai cho khách hàng mới.")
    log(dung, -2, 11, activity_type="call", opportunity_id=d, contact_id=ct["Trịnh Thu Hà"],
        content="Trao đổi về điều khoản thanh toán.", outcome="Khách đồng ý thanh toán theo quý.",
        duration_minutes=15)

    # Cơ hội E – nhóm Miền Nam, đang đàm phán
    e = create(giang, -40, name="Hệ thống quản lý vận tải", customer_id=cu["sao_viet"],
               primary_contact_id=ct["Đặng Hoài Nam"], estimated_value=400_000_000, expected_close_date=day(10),
               source="event")
    log(giang, -38, 16, activity_type="meeting", opportunity_id=e, content="Khảo sát nhu cầu quản lý đội xe.",
        outcome="Khách cần tích hợp với phần mềm kế toán.", occurred_at=day(-38, "14:00:00"),
        duration_minutes=120)
    move(giang, e, "qualification", -37)
    move(giang, e, "proposal", -35)
    add(giang, e, -34, product_id=pr["CRM-PRO"], quantity=30, periods=12)
    add(giang, e, -34, product_id=pr["MC-NAM"], quantity=1, periods=2)
    add(giang, e, -34, product_id=pr["HT-QUY"], quantity=1, periods=8)
    move(giang, e, "quotation", -30)
    move(giang, e, "negotiation", -8)
    log(giang, -3, 10, activity_type="call", opportunity_id=e,
        content="Thương lượng chiết khấu cho hợp đồng 2 năm.", outcome="Chờ khách xác nhận mức chiết khấu 5%.",
        duration_minutes=20)

    # Cơ hội F – trưởng nhóm tạo thẳng ở giai đoạn Đề xuất, ghi đè điều kiện kèm lý do
    create(binh, -5, name="CRM cho hệ thống trường", customer_id=cu["minh_tri"],
           primary_contact_id=ct["Lý Thanh Tâm"], stage_id=st["proposal"], estimated_value=500_000_000,
           expected_close_date=day(60), source="event", override=True,
           override_reason="Đã gặp ban giám đốc tại hội thảo giáo dục, biên bản đã gửi qua email.")

    # Cơ hội G – đã thắng
    g = create(giang, -50, name="Thuê máy chủ lưu trữ 2 năm", customer_id=cu["phu_thanh"],
               primary_contact_id=ct["Phan Văn Lộc"], estimated_value=48_000_000, expected_close_date=day(-20),
               source="partner")
    log(giang, -49, 15, activity_type="meeting", opportunity_id=g, content="Tư vấn phương án lưu trữ dữ liệu.",
        outcome="Khách chọn gói thuê 2 năm.", occurred_at=day(-49, "09:00:00"), duration_minutes=60)
    move(giang, g, "qualification", -48)
    move(giang, g, "proposal", -47)
    add(giang, g, -46, product_id=pr["MC-NAM"], quantity=1, periods=2)
    move(giang, g, "won", -21)

    # Cơ hội H – đã thua
    h = create(dung, -25, name="Máy in hoá đơn cho chi nhánh", customer_id=cu["an_khang"],
               primary_contact_id=ct["Trịnh Thu Hà"], estimated_value=18_000_000, expected_close_date=day(-10),
               source="existing_customer")
    move(dung, h, "lost", -10)

    # SCRUM-99: lịch hẹn sắp tới và lịch hẹn cần cập nhật kết quả
    at(-1, 9)
    activities.create_activity(cuong, {
        "activity_type": "call", "opportunity_id": c, "contact_id": ct["Bùi Văn Khoa"],
        "subject": "Gọi xác nhận nhu cầu gia hạn hỗ trợ",
        "occurred_at": (base - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S"), "duration_minutes": 15})
    activities.create_activity(cuong, {
        "activity_type": "meeting", "opportunity_id": a, "subject": "Thương lượng báo giá điều chỉnh",
        "occurred_at": day(1, "09:00:00"), "duration_minutes": 60})

    # SCRUM-100: công việc có hạn
    friday = base.date() + timedelta(days=(4 - base.weekday()) % 7)
    at(-1, 10)
    tasks.create_task(cuong, {"title": "Gửi báo giá điều chỉnh cho Ánh Dương", "due_date": friday.isoformat(),
                              "priority": "high", "opportunity_id": a,
                              "description": "Đã hứa gửi khách bản báo giá điều chỉnh chiết khấu vào thứ Sáu."})
    at(-8)
    late = tasks.create_task(cuong, {"title": "Gọi lại anh Khoa về gói hỗ trợ năm 2027", "due_date": day(-5),
                                     "priority": "medium", "opportunity_id": c})["task"]["id"]
    at(-6, 17)
    tasks.postpone_task(cuong, late, {"new_due_date": day(-3), "reason": "Khách đi công tác, hẹn gọi lại sau."})
    at(-2)
    tasks.create_task(binh, {"title": "Chuẩn bị demo trên dữ liệu thật cho An Khang", "due_date": day(3),
                             "priority": "urgent", "assignee_id": dung["id"], "opportunity_id": d})
    at(-14)
    done = tasks.create_task(dung, {"title": "Gửi tài liệu giới thiệu giải pháp", "due_date": day(-10),
                                    "priority": "low", "opportunity_id": d})["task"]["id"]
    at(-11, 15)
    tasks.complete_task(dung, done, {"note": "Đã gửi qua email cho anh Tuấn."})
    at(-1, 14)
    tasks.create_task(giang, {"title": "Xác nhận điều khoản thanh toán với Sao Việt", "due_date": day(2),
                              "priority": "high", "opportunity_id": e})


def seed_all() -> None:
    """Tạo dữ liệu nền (mốc 90 ngày trước) và luồng nghiệp vụ mẫu."""
    previous = clock.frozen_at()
    base = clock.now()
    try:
        clock.freeze(base - timedelta(days=90))
        ids = seed_base()
        seed_demo(ids, base)
    finally:
        if previous is None:
            clock.unfreeze()
        else:
            clock.freeze(previous)
    commit()


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    reset = "--reset" in sys.argv[1:]
    from app import create_app

    app = create_app({"AUTO_INIT_DB": False})
    with app.app_context():
        if reset:
            drop_all()
        init_db()
        if not is_empty():
            print("CSDL đã có dữ liệu nên không tạo thêm. Dùng: python -m app.seed --reset để xoá và tạo lại.")
            return
        seed_all()
        print(f"Đã tạo dữ liệu mẫu tại: {app.config['DATABASE']}")
        print(f"Tài khoản mẫu (mật khẩu chung: {DEMO_PASSWORD}):")
        for username, full_name, _, role, _ in USERS:
            from app.labels import ROLES
            print(f"  - {username:<12} {full_name:<20} {ROLES[role]}")


if __name__ == "__main__":
    main()
