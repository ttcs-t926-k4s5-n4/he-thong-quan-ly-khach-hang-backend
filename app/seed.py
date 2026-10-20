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
