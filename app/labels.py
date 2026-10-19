"""Nhãn tiếng Việt cho các giá trị mã hoá và các hàm định dạng hiển thị."""
from __future__ import annotations

import unicodedata
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

ROLES = {
    "staff": "Nhân viên kinh doanh",
    "team_lead": "Trưởng nhóm",
    "director": "Giám đốc kinh doanh",
    "admin": "Quản trị hệ thống",
}

OPPORTUNITY_SOURCES = {
    "website": "Website",
    "referral": "Khách hàng giới thiệu",
    "event": "Sự kiện / hội thảo",
    "cold_call": "Gọi điện chủ động",
    "campaign": "Chiến dịch marketing",
    "partner": "Đối tác",
    "existing_customer": "Khách hàng hiện hữu",
    "other": "Khác",
}
OPPORTUNITY_STATUSES = {"open": "Đang mở", "won": "Đã thắng", "lost": "Đã thua"}
AMOUNT_SOURCES = {"manual": "Nhập tay (ước lượng)", "lines": "Tính tự động từ dòng sản phẩm"}

PRODUCT_TYPES = {"product": "Sản phẩm", "service": "Dịch vụ", "subscription": "Dịch vụ thuê bao"}
BILLING_PERIODS = {"month": "Tháng", "quarter": "Quý", "year": "Năm"}
PERIODS_PER_YEAR = {"month": 12, "quarter": 4, "year": 1}
MONTHS_PER_PERIOD = {"month": 1, "quarter": 3, "year": 12}

ACTIVITY_TYPES = {"call": "Cuộc gọi", "meeting": "Cuộc gặp", "email": "Email", "note": "Ghi chú"}
ACTIVITY_STATUSES = {"completed": "Đã diễn ra", "planned": "Sắp diễn ra"}
LOGGED_VIA = {"web": "Ứng dụng web", "mobile": "Điện thoại (ghi nhanh)"}

TASK_PRIORITIES = {"low": "Thấp", "medium": "Trung bình", "high": "Cao", "urgent": "Khẩn cấp"}
TASK_STATUSES = {"open": "Chưa hoàn thành", "done": "Đã hoàn thành"}

RULE_TYPES = {
    "min_activities": "Tối thiểu số hoạt động đã diễn ra",
    "required_field": "Bắt buộc có thông tin",
    "min_product_lines": "Tối thiểu số dòng sản phẩm/dịch vụ",
    "min_amount": "Giá trị cơ hội tối thiểu",
}
RULE_FIELDS = {"primary_contact_id": "Người liên hệ chính", "description": "Mô tả nhu cầu"}

WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def choices_out(mapping: dict) -> list[dict]:
    return [{"value": key, "label": label} for key, label in mapping.items()]


def round_vnd(value) -> int:
    """Làm tròn về số nguyên đồng (làm tròn nửa lên)."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_vnd(value) -> str:
    return f"{int(value):,}".replace(",", ".") + " đ"


def format_number(value) -> str:
    """Định dạng số kiểu Việt Nam: 1.500 hoặc 2,5."""
    number = Decimal(str(value)).normalize()
    if number == number.to_integral_value():
        return f"{int(number):,}".replace(",", ".")
    integer_part, fraction = f"{number:f}".split(".")
    return f"{int(integer_part):,}".replace(",", ".") + "," + fraction


def number_out(value):
    """Trả số cho JSON: số nguyên nếu không có phần lẻ."""
    if value is None:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return value


def format_date(value) -> str:
    return _as_date(value).strftime("%d/%m/%Y")


def format_date_weekday(value) -> str:
    day = _as_date(value)
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d/%m/%Y')}"


def format_datetime(value) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("T", " "))
    return value.strftime("%d/%m/%Y %H:%M")


def search_text(value: str | None) -> str | None:
    """Chuẩn hoá chuỗi để tìm kiếm: chữ thường, bỏ dấu tiếng Việt (đ -> d)."""
    if value is None:
        return None
    text = unicodedata.normalize("NFD", str(value).lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")
