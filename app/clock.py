"""Đồng hồ hệ thống theo giờ Việt Nam (UTC+7).

Mọi thời điểm lưu trong CSDL là giờ Việt Nam, dạng chuỗi "YYYY-MM-DD HH:MM:SS".
Khi kiểm thử hoặc tạo dữ liệu mẫu có thể "đóng băng" thời gian bằng freeze().
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")
DB_FORMAT = "%Y-%m-%d %H:%M:%S"

_frozen: datetime | None = None


def now() -> datetime:
    """Thời điểm hiện tại theo giờ Việt Nam (không kèm múi giờ, chính xác tới giây)."""
    if _frozen is not None:
        return _frozen
    return datetime.now(VN_TZ).replace(tzinfo=None, microsecond=0)


def today() -> date:
    return now().date()


def freeze(moment: datetime) -> None:
    """Cố định thời điểm hiện tại (dùng cho kiểm thử và dữ liệu mẫu)."""
    global _frozen
    _frozen = moment.replace(microsecond=0)


def unfreeze() -> None:
    global _frozen
    _frozen = None


def frozen_at() -> datetime | None:
    """Thời điểm đang bị đóng băng (None nếu đồng hồ chạy thật)."""
    return _frozen


def to_db(moment: datetime) -> str:
    return moment.strftime(DB_FORMAT)


def from_db(text: str | None) -> datetime | None:
    if not text:
        return None
    return datetime.strptime(text, DB_FORMAT)


def iso(text: str | None) -> str | None:
    """Chuyển chuỗi thời gian trong CSDL sang dạng ISO 8601 để trả về API."""
    if not text:
        return None
    return text.replace(" ", "T", 1)


def to_vn_naive(moment: datetime) -> datetime:
    """Quy đổi thời điểm có múi giờ về giờ Việt Nam (bỏ thông tin múi giờ)."""
    if moment.tzinfo is not None:
        moment = moment.astimezone(VN_TZ).replace(tzinfo=None)
    return moment.replace(microsecond=0)
