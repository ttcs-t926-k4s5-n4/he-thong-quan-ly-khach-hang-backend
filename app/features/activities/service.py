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
    return {"message": _created_message(prepared), "activity": activity_out(_fetch(activity_id))}


def quick_log(user: dict, payload: dict) -> dict:
    """Ghi nhanh trên điện thoại ngay sau buổi làm việc với khách."""
    data = validate(payload, QUICK_SCHEMA)
    duration = None if data["activity_type"] == "note" else data["duration_minutes"]
    started = clock.now() - timedelta(minutes=data["ended_minutes_ago"] + (duration or 0))
    prepared = _prepare(user, {**data, "occurred_at": started, "status": "completed"})
    activity_id = _insert(user, prepared, "mobile")

    follow_up = None
    if data["follow_up_task"] is not None:
        from app.features.tasks import service as tasks  # liên kết với SCRUM-100

        task_payload = {key: value for key, value in data["follow_up_task"].items()
                        if key in ("title", "due_date", "priority", "description")}
        task_payload.update({"customer_id": prepared["customer"]["id"], "opportunity_id": prepared["opportunity_id"]})
        try:
            follow_up = tasks.create_task(user, task_payload, source_activity_id=activity_id)["task"]
        except ValidationFailed as exc:
            errors = [field_error(f"follow_up_task.{e['field']}", e["label"], e["message"]) for e in exc.errors]
            raise ValidationFailed(errors) from None

    message = _created_message(prepared)
    if follow_up:
        message += f" Đã tạo công việc tiếp theo \"{follow_up['title']}\", hạn {follow_up['due_date_display']}."
    return {"message": message, "activity": activity_out(_fetch(activity_id)), "follow_up_task": follow_up}


def list_activities(user: dict, args: dict) -> dict:
    params = validate(args, LIST_SCHEMA)
    scope, values = activity_scope(user)
    return _list(scope, values, params)


def customer_timeline(user: dict, customer_id: int, args: dict) -> dict:
    """Toàn bộ lịch sử trao đổi với một khách hàng – ai trong phạm vi quyền cũng xem được, kể cả do người khác ghi."""
    scope, scope_params = owner_scope(user, "c.owner_id")
    customer = row(f"SELECT c.id, c.name FROM customers c WHERE c.id = ? AND {scope}", (customer_id, *scope_params))
    if customer is None:
        raise NotFound("Không tìm thấy khách hàng hoặc bạn không có quyền với khách hàng này.")
    params = validate(args, LIST_SCHEMA)
    params["customer_id"] = customer_id
    result = _list("1=1", [], params)
    counts = rows("SELECT activity_type, COUNT(*) AS total FROM activities WHERE customer_id = ? "
                  "GROUP BY activity_type", (customer_id,))
    count_map = {r["activity_type"]: r["total"] for r in counts}
    last = scalar("SELECT MAX(occurred_at) FROM activities WHERE customer_id = ? AND status = 'completed'",
                  (customer_id,))
    result["customer"] = customer
    result["summary"] = {
        "total": sum(count_map.values()),
        "by_type": [{"activity_type": key, "label": label, "count": count_map.get(key, 0)}
                    for key, label in ACTIVITY_TYPES.items()],
        "last_activity_at": clock.iso(last),
    }
    return result


def _list(scope: str, values: list, params: dict) -> dict:
    where, values = [scope], list(values)
    for column in ("customer_id", "opportunity_id", "contact_id", "owner_id", "activity_type", "status"):
        if params.get(column) is not None:
            where.append(f"a.{column} = ?")
            values.append(params[column])
    if params.get("date_from"):
        where.append("a.occurred_at >= ?")
        values.append(f"{params['date_from'].isoformat()} 00:00:00")
    if params.get("date_to"):
        where.append("a.occurred_at <= ?")
        values.append(f"{params['date_to'].isoformat()} 23:59:59")
    if params.get("q"):
        where.append("(search_text(a.content) LIKE ? OR search_text(a.subject) LIKE ? "
                     "OR search_text(a.outcome) LIKE ?)")
        keyword = f"%{search_text(params['q'])}%"
        values += [keyword, keyword, keyword]
    condition = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM ({ACTIVITY_SELECT} WHERE {condition})", values)
    limit, offset = page_window(params)
    items = rows(ACTIVITY_SELECT + f" WHERE {condition} ORDER BY a.occurred_at DESC, a.id DESC LIMIT ? OFFSET ?",
                 [*values, limit, offset])
    return page_result([activity_out(a) for a in items], total, params)


def _check_can_modify(user: dict, activity: dict) -> None:
    if activity["owner_id"] != user["id"] and not at_least(user, "team_lead"):
        raise Forbidden("Bạn chỉ được sửa hoặc xoá hoạt động do chính mình ghi nhận.")


def update_activity(user: dict, activity_id: int, payload: dict) -> dict:
    activity = get_visible_activity(user, activity_id)
    _check_can_modify(user, activity)
    changes = validate(payload, CREATE_SCHEMA, partial=True)
    if not changes:
        raise invalid("body", "Dữ liệu", "Không có thông tin nào để cập nhật.")
    merged = {key: activity[key] for key in ("activity_type", "customer_id", "contact_id", "opportunity_id",
                                             "subject", "content", "outcome", "duration_minutes", "status")}
    merged["occurred_at"] = clock.from_db(activity["occurred_at"])
    if "customer_id" in changes and "opportunity_id" not in changes and changes["customer_id"] != activity["customer_id"]:
        merged["opportunity_id"] = None
        merged["contact_id"] = None
    merged.update(changes)
    time_changed = "status" in changes or "occurred_at" in changes
    if "status" not in changes and "occurred_at" in changes:
        merged["status"] = None  # tính lại trạng thái theo thời điểm mới
    prepared = _prepare(user, merged, strict_time=time_changed)
    execute("UPDATE activities SET activity_type = ?, status = ?, subject = ?, content = ?, outcome = ?, "
            "occurred_at = ?, duration_minutes = ?, customer_id = ?, contact_id = ?, opportunity_id = ?, "
            "updated_at = ? WHERE id = ?",
            (prepared["activity_type"], prepared["status"], prepared["subject"], prepared["content"],
             prepared["outcome"], clock.to_db(prepared["occurred_at"]), prepared["duration_minutes"],
             prepared["customer"]["id"], prepared["contact_id"], prepared["opportunity_id"],
             clock.to_db(clock.now()), activity_id))
    return {"message": f"Đã cập nhật {ACTIVITY_TYPES[prepared['activity_type']].lower()} với "
                       f"{prepared['customer']['name']}.", "activity": activity_out(_fetch(activity_id))}


def complete_activity(user: dict, activity_id: int, payload: dict) -> dict:
    """Cập nhật kết quả cho cuộc gọi/cuộc gặp đã lên lịch sau khi diễn ra."""
    activity = get_visible_activity(user, activity_id)
    _check_can_modify(user, activity)
    if activity["status"] == "completed":
        raise Conflict("Hoạt động này đã được ghi nhận là đã diễn ra.")
    data = validate(payload, COMPLETE_SCHEMA)
    now = clock.now()
    duration = data["duration_minutes"] if data["duration_minutes"] is not None else activity["duration_minutes"]
    planned_at = clock.from_db(activity["occurred_at"])
    if data["occurred_at"] is not None:
        occurred = data["occurred_at"]
    elif planned_at <= now:
        occurred = planned_at
    else:
        occurred = now - timedelta(minutes=duration or 0)
    if occurred > now + FUTURE_TOLERANCE:
        raise invalid("occurred_at", "Thời điểm", "Hoạt động đã diễn ra không thể có thời điểm ở tương lai.")
    content = data["content"] or activity["content"]
    if not content:
        raise invalid("content", "Nội dung trao đổi", "Vui lòng nhập nội dung trao đổi cho hoạt động đã diễn ra.")
    execute("UPDATE activities SET status = 'completed', content = ?, outcome = ?, duration_minutes = ?, "
            "occurred_at = ?, updated_at = ? WHERE id = ?",
            (content, data["outcome"] or activity["outcome"], duration, clock.to_db(occurred),
             clock.to_db(now), activity_id))
    kind = ACTIVITY_TYPES[activity["activity_type"]].lower()
    return {"message": f"Đã cập nhật kết quả {kind} với {activity['customer_name']}.",
            "activity": activity_out(_fetch(activity_id))}


def delete_activity(user: dict, activity_id: int) -> dict:
    activity = get_visible_activity(user, activity_id)
    _check_can_modify(user, activity)
    if scalar("SELECT COUNT(*) FROM tasks WHERE source_activity_id = ?", (activity_id,)):
        execute("UPDATE tasks SET source_activity_id = NULL WHERE source_activity_id = ?", (activity_id,))
    execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    kind = ACTIVITY_TYPES[activity["activity_type"]].lower()
    return {"message": f"Đã xoá {kind} với {activity['customer_name']}."}


def _compact(activity: dict) -> dict:
    occurred = clock.from_db(activity["occurred_at"])
    return {
        "id": activity["id"],
        "activity_type": activity["activity_type"],
        "activity_type_label": ACTIVITY_TYPES[activity["activity_type"]],
        "status": activity["status"],
        "occurred_at": clock.iso(activity["occurred_at"]),
        "time_display": occurred.strftime("%H:%M"),
        "date_display": occurred.strftime("%d/%m/%Y"),
        "subject": activity["subject"],
        "customer": {"id": activity["customer_id"], "name": activity["customer_name"]},
        "contact_name": activity["contact_name"],
        "opportunity": ({"id": activity["opportunity_id"], "name": activity["opportunity_name"]}
                        if activity["opportunity_id"] else None),
    }


def quick_suggestions(user: dict) -> dict:
    """Dữ liệu gọn cho màn hình ghi nhanh trên điện thoại."""
    now = clock.now()
    start = datetime.combine(now.date() - timedelta(days=2), datetime.min.time())
    end = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    needs_result = rows(ACTIVITY_SELECT + " WHERE a.owner_id = ? AND a.status = 'planned' "
                        "AND a.occurred_at >= ? AND a.occurred_at < ? ORDER BY a.occurred_at",
                        (user["id"], clock.to_db(start), clock.to_db(end)))
    open_opps = rows(
        "SELECT o.id, o.name, o.customer_id, c.name AS customer_name, s.name AS stage_name, o.expected_close_date "
        "FROM opportunities o JOIN customers c ON c.id = o.customer_id JOIN pipeline_stages s ON s.id = o.stage_id "
        "WHERE o.owner_id = ? AND o.is_deleted = 0 AND s.is_won = 0 AND s.is_lost = 0 "
        "ORDER BY o.expected_close_date, o.id LIMIT 10", (user["id"],))
    scope, params = owner_scope(user, "c.owner_id")
    recent_customers = rows(
        "SELECT c.id, c.name, MAX(a.occurred_at) AS last_activity_at FROM customers c "
        "LEFT JOIN activities a ON a.customer_id = c.id AND a.owner_id = ? "
        f"WHERE {scope} GROUP BY c.id, c.name "
        "ORDER BY last_activity_at IS NULL, last_activity_at DESC, c.name LIMIT 8", (user["id"], *params))
    return {
        "needs_result": [_compact(a) for a in needs_result],
        "open_opportunities": [{
            "id": o["id"], "name": o["name"], "stage_name": o["stage_name"],
            "customer": {"id": o["customer_id"], "name": o["customer_name"]},
            "expected_close_date": o["expected_close_date"],
        } for o in open_opps],
        "recent_customers": [{"id": c["id"], "name": c["name"],
                              "last_activity_at": clock.iso(c["last_activity_at"])} for c in recent_customers],
        "activity_types": choices_out(ACTIVITY_TYPES),
    }
