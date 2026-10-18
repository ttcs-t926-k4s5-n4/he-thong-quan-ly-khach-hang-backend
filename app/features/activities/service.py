"""SCRUM-99 – Ghi nhận hoạt động với khách hàng (lịch sử trao đổi dùng chung, không nằm trong hộp thư cá nhân).

Tiêu chí:
- Loại hoạt động: cuộc gọi, cuộc gặp, email, ghi chú.
- Gắn hoạt động với khách hàng, người liên hệ và cơ hội liên quan.
- Ghi thời điểm, thời lượng, nội dung trao đổi và kết quả.
- Ghi được hoạt động đã diễn ra trong quá khứ, không chỉ hoạt động sắp tới.
- Dùng được nhanh trên điện thoại ngay sau khi rời văn phòng khách:
  POST /api/activities/quick chỉ cần loại + cơ hội (hoặc khách hàng) + nội dung; thời điểm tự tính
  từ thời lượng và "kết thúc cách đây bao nhiêu phút"; có thể tạo luôn công việc tiếp theo.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app import clock
from app.common.access import resolve_customer_links
from app.db import execute, row, rows, scalar
from app.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.labels import (ACTIVITY_STATUSES, ACTIVITY_TYPES, LOGGED_VIA, choices_out, format_datetime,
                        search_text)
from app.permissions import at_least, owner_scope, sees_everything
from app.validation import (PAGINATION, Choice, DateField, DateTimeField, Int, Obj, Str, field_error, invalid,
                            page_result, page_window, validate)

MIN_OCCURRED_AT = datetime(2000, 1, 1)
FUTURE_TOLERANCE = timedelta(minutes=5)

CREATE_SCHEMA = {
    "activity_type": Choice("Loại hoạt động", ACTIVITY_TYPES, required=True),
    "customer_id": Int("Khách hàng", min_value=1),
    "contact_id": Int("Người liên hệ", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
    "subject": Str("Tiêu đề", max_len=255),
    "content": Str("Nội dung trao đổi", max_len=5000),
    "outcome": Str("Kết quả", max_len=2000),
    "occurred_at": DateTimeField("Thời điểm"),
    "duration_minutes": Int("Thời lượng (phút)", min_value=0, max_value=1440),
    "status": Choice("Trạng thái", ACTIVITY_STATUSES),
}

QUICK_SCHEMA = {
    "activity_type": Choice("Loại hoạt động", ACTIVITY_TYPES, default="meeting"),
    "customer_id": Int("Khách hàng", min_value=1),
    "contact_id": Int("Người liên hệ", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
    "content": Str("Nội dung trao đổi", required=True, min_len=1, max_len=5000),
    "outcome": Str("Kết quả", max_len=2000),
    "duration_minutes": Int("Thời lượng (phút)", min_value=0, max_value=1440),
    "ended_minutes_ago": Int("Kết thúc cách đây (phút)", min_value=0, max_value=1440, default=0),
    "follow_up_task": Obj("Công việc tiếp theo"),
}

COMPLETE_SCHEMA = {
    "content": Str("Nội dung trao đổi", max_len=5000),
    "outcome": Str("Kết quả", max_len=2000),
    "duration_minutes": Int("Thời lượng (phút)", min_value=0, max_value=1440),
    "occurred_at": DateTimeField("Thời điểm"),
}

LIST_SCHEMA = {
    "customer_id": Int("Khách hàng", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
    "contact_id": Int("Người liên hệ", min_value=1),
    "owner_id": Int("Người ghi nhận", min_value=1),
    "activity_type": Choice("Loại hoạt động", ACTIVITY_TYPES),
    "status": Choice("Trạng thái", ACTIVITY_STATUSES),
    "date_from": DateField("Từ ngày"),
    "date_to": DateField("Đến ngày"),
    "q": Str("Từ khoá", max_len=100),
    **PAGINATION,
}

ACTIVITY_SELECT = """
SELECT a.*, c.name AS customer_name, ct.full_name AS contact_name, o.name AS opportunity_name,
       u.full_name AS owner_name
FROM activities a
JOIN customers c ON c.id = a.customer_id
LEFT JOIN contacts ct ON ct.id = a.contact_id
LEFT JOIN opportunities o ON o.id = a.opportunity_id
JOIN users u ON u.id = a.owner_id
"""


def activity_scope(user: dict) -> tuple[str, list]:
    """Thấy hoạt động do mình ghi, hoặc thuộc khách hàng/cơ hội trong phạm vi quyền (lịch sử dùng chung)."""
    if sees_everything(user):
        return "1=1", []
    s1, p1 = owner_scope(user, "a.owner_id")
    s2, p2 = owner_scope(user, "c.owner_id")
    s3, p3 = owner_scope(user, "o.owner_id")
    return f"(({s1}) OR ({s2}) OR (o.id IS NOT NULL AND {s3}))", p1 + p2 + p3


def activity_out(activity: dict) -> dict:
    occurred = clock.from_db(activity["occurred_at"])
    return {
        "id": activity["id"],
        "activity_type": activity["activity_type"],
        "activity_type_label": ACTIVITY_TYPES[activity["activity_type"]],
        "status": activity["status"],
        "status_label": ACTIVITY_STATUSES[activity["status"]],
        "subject": activity["subject"],
        "content": activity["content"],
        "outcome": activity["outcome"],
        "occurred_at": clock.iso(activity["occurred_at"]),
        "occurred_at_display": format_datetime(occurred),
        "duration_minutes": activity["duration_minutes"],
        "customer": {"id": activity["customer_id"], "name": activity["customer_name"]},
        "contact": ({"id": activity["contact_id"], "full_name": activity["contact_name"]}
                    if activity["contact_id"] else None),
        "opportunity": ({"id": activity["opportunity_id"], "name": activity["opportunity_name"]}
                        if activity["opportunity_id"] else None),
        "owner": {"id": activity["owner_id"], "full_name": activity["owner_name"]},
        "logged_via": activity["logged_via"],
        "logged_via_label": LOGGED_VIA[activity["logged_via"]],
        "created_at": clock.iso(activity["created_at"]),
        "updated_at": clock.iso(activity["updated_at"]),
    }


def _fetch(activity_id: int) -> dict:
    return row(ACTIVITY_SELECT + " WHERE a.id = ?", (activity_id,))


def get_visible_activity(user: dict, activity_id: int) -> dict:
    scope, params = activity_scope(user)
    activity = row(ACTIVITY_SELECT + f" WHERE a.id = ? AND {scope}", (activity_id, *params))
    if activity is None:
        raise NotFound("Không tìm thấy hoạt động hoặc bạn không có quyền xem hoạt động này.")
    return activity


def _determine_status(activity_type: str, occurred: datetime, status: str | None,
                      strict_time: bool = True) -> str:
    """Hoạt động trong quá khứ là 'đã diễn ra'; trong tương lai là 'sắp diễn ra' (chỉ cuộc gọi/cuộc gặp).

    strict_time=False: khi chỉ sửa nội dung của lịch hẹn đã qua giờ thì không bắt thời điểm ở tương lai.
    """
    now = clock.now()
    if occurred < MIN_OCCURRED_AT:
        raise invalid("occurred_at", "Thời điểm", "Thời điểm hoạt động không hợp lệ.")
    if status is None:
        status = "completed" if occurred <= now else "planned"
    if status == "completed" and occurred > now + FUTURE_TOLERANCE:
        raise invalid("occurred_at", "Thời điểm", "Hoạt động đã diễn ra không thể có thời điểm ở tương lai.")
    if status == "planned":
        if activity_type not in ("call", "meeting"):
            raise invalid("occurred_at", "Thời điểm",
                          f"{ACTIVITY_TYPES[activity_type]} không thể lên lịch trước; chỉ cuộc gọi hoặc cuộc gặp "
                          "mới có thời điểm trong tương lai.")
        if occurred <= now and strict_time:
            raise invalid("occurred_at", "Thời điểm", "Hoạt động sắp diễn ra phải có thời điểm trong tương lai.")
    return status


def _prepare(user: dict, data: dict, *, strict_time: bool = True) -> dict:
    """Kiểm tra liên kết, thời điểm, trạng thái, nội dung và chuẩn hoá dữ liệu để lưu."""
    customer, contact, opp = resolve_customer_links(user, data.get("customer_id"), data.get("contact_id"),
                                                    data.get("opportunity_id"))
    occurred = data.get("occurred_at") or clock.now()
    status = _determine_status(data["activity_type"], occurred, data.get("status"), strict_time)
    if status == "completed" and not data.get("content"):
        raise invalid("content", "Nội dung trao đổi", "Vui lòng nhập nội dung trao đổi cho hoạt động đã diễn ra.")
    return {
        "activity_type": data["activity_type"],
        "status": status,
        "subject": data.get("subject"),
        "content": data.get("content"),
        "outcome": data.get("outcome"),
        "occurred_at": occurred,
        "duration_minutes": None if data["activity_type"] == "note" else data.get("duration_minutes"),
        "customer": customer,
        "contact_id": contact["id"] if contact else None,
        "opportunity_id": opp["id"] if opp else None,
    }


def _insert(user: dict, prepared: dict, logged_via: str) -> int:
    now_text = clock.to_db(clock.now())
    return execute(
        "INSERT INTO activities (activity_type, status, subject, content, outcome, occurred_at, duration_minutes, "
        "customer_id, contact_id, opportunity_id, owner_id, logged_via, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (prepared["activity_type"], prepared["status"], prepared["subject"], prepared["content"],
         prepared["outcome"], clock.to_db(prepared["occurred_at"]), prepared["duration_minutes"],
         prepared["customer"]["id"], prepared["contact_id"], prepared["opportunity_id"], user["id"], logged_via,
         now_text, now_text))


def _created_message(prepared: dict) -> str:
    kind = ACTIVITY_TYPES[prepared["activity_type"]].lower()
    when = format_datetime(prepared["occurred_at"])
    customer = prepared["customer"]["name"]
    if prepared["status"] == "planned":
        return f"Đã lên lịch {kind} với {customer} lúc {when}."
    if prepared["activity_type"] == "note":
        return f"Đã thêm ghi chú cho khách hàng {customer} ({when})."
    duration = f", {prepared['duration_minutes']} phút" if prepared["duration_minutes"] else ""
    return f"Đã ghi nhận {kind} với {customer} lúc {when}{duration}."


def create_activity(user: dict, payload: dict) -> dict:
    prepared = _prepare(user, validate(payload, CREATE_SCHEMA))
    activity_id = _insert(user, prepared, "web")
