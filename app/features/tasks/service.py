"""SCRUM-100 – Tạo và theo dõi công việc có hạn hoàn thành.

Tiêu chí:
- Công việc có tiêu đề, hạn, mức ưu tiên, người thực hiện, gắn với khách hàng hoặc cơ hội.
- Đánh dấu hoàn thành; hoãn kèm lý do (lưu lịch sử hoãn).
- Trưởng nhóm giao việc được cho thành viên trong nhóm.

Quy tắc bổ sung:
- Nhân viên chỉ tạo công việc cho chính mình; Giám đốc/Quản trị giao được cho mọi người.
- Muốn lùi hạn phải dùng chức năng Hoãn (bắt buộc lý do), không sửa trực tiếp hạn sang ngày muộn hơn.
"""
from __future__ import annotations

from datetime import date, timedelta

from app import clock
from app.common.access import get_active_user, resolve_customer_links
from app.db import execute, row, rows, scalar
from app.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.labels import (TASK_PRIORITIES, TASK_STATUSES, format_date, format_date_weekday, search_text)
from app.permissions import at_least, owner_scope
from app.validation import (PAGINATION, Bool, Choice, DateField, Int, Str, field_error, invalid,
                            page_result, page_window, validate)

CREATE_SCHEMA = {
    "title": Str("Tiêu đề công việc", required=True, min_len=1, max_len=255),
    "description": Str("Mô tả", max_len=4000),
    "due_date": DateField("Hạn hoàn thành", required=True),
    "priority": Choice("Mức ưu tiên", TASK_PRIORITIES, default="medium"),
    "assignee_id": Int("Người thực hiện", min_value=1),
    "customer_id": Int("Khách hàng", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
}

UPDATE_SCHEMA = {
    "title": Str("Tiêu đề công việc", required=True, min_len=1, max_len=255),
    "description": Str("Mô tả", max_len=4000),
    "due_date": DateField("Hạn hoàn thành", nullable=False),
    "priority": Choice("Mức ưu tiên", TASK_PRIORITIES, nullable=False),
    "customer_id": Int("Khách hàng", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
}
UPDATE_FORBIDDEN = {
    "assignee_id": "Đổi người thực hiện bằng chức năng giao việc (POST /api/tasks/{id}/assign).",
    "status": "Dùng chức năng hoàn thành / mở lại công việc để đổi trạng thái.",
}

POSTPONE_SCHEMA = {
    "new_due_date": DateField("Hạn mới", required=True),
    "reason": Str("Lý do hoãn", required=True, min_len=5, max_len=1000),
}
COMPLETE_SCHEMA = {"note": Str("Ghi chú hoàn thành", max_len=2000)}
ASSIGN_SCHEMA = {"assignee_id": Int("Người thực hiện", required=True, min_value=1)}

DUE_FILTERS = {"overdue": "Quá hạn", "today": "Đến hạn hôm nay", "next_7_days": "Trong 7 ngày tới"}
LIST_SCHEMA = {
    "status": Choice("Trạng thái", {**TASK_STATUSES, "all": "Tất cả"}, default="open"),
    "assigned_to_me": Bool("Chỉ việc giao cho tôi", default=False),
    "assignee_id": Int("Người thực hiện", min_value=1),
    "customer_id": Int("Khách hàng", min_value=1),
    "opportunity_id": Int("Cơ hội", min_value=1),
    "priority": Choice("Mức ưu tiên", TASK_PRIORITIES),
    "due": Choice("Hạn", DUE_FILTERS),
    "due_from": DateField("Hạn từ ngày"),
    "due_to": DateField("Hạn đến ngày"),
    "q": Str("Từ khoá", max_len=100),
    **PAGINATION,
}

TASK_SELECT = """
SELECT t.*, ua.full_name AS assignee_name, ua.team_id AS assignee_team_id, uc.full_name AS creator_name,
       c.name AS customer_name, o.name AS opportunity_name,
       (SELECT p.reason FROM task_postponements p WHERE p.task_id = t.id ORDER BY p.id DESC LIMIT 1)
           AS last_postpone_reason
FROM tasks t
JOIN users ua ON ua.id = t.assignee_id
JOIN users uc ON uc.id = t.created_by
LEFT JOIN customers c ON c.id = t.customer_id
LEFT JOIN opportunities o ON o.id = t.opportunity_id
"""

PRIORITY_ORDER = "CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"


def task_scope(user: dict) -> tuple[str, list]:
    """Nhân viên: việc mình làm hoặc mình tạo; trưởng nhóm: việc của nhóm; giám đốc: tất cả."""
    s1, p1 = owner_scope(user, "t.assignee_id")
    s2, p2 = owner_scope(user, "t.created_by")
    return f"(({s1}) OR ({s2}))", p1 + p2


def task_out(task: dict, today: date | None = None) -> dict:
    today = today or clock.today()
    due = date.fromisoformat(task["due_date"])
    is_open = task["status"] == "open"
    overdue = is_open and due < today
    if not is_open:
        due_state, due_label = "done", "Đã hoàn thành"
    elif overdue:
        due_state, due_label = "overdue", f"Quá hạn {(today - due).days} ngày"
    elif due == today:
        due_state, due_label = "today", "Đến hạn hôm nay"
    else:
        due_state, due_label = "upcoming", f"Còn {(due - today).days} ngày"
    return {
        "id": task["id"],
        "title": task["title"],
        "description": task["description"],
        "due_date": task["due_date"],
        "due_date_display": format_date_weekday(due),
        "due_state": due_state,
        "due_state_label": due_label,
        "is_overdue": overdue,
        "priority": task["priority"],
        "priority_label": TASK_PRIORITIES[task["priority"]],
        "status": task["status"],
        "status_label": TASK_STATUSES[task["status"]],
        "assignee": {"id": task["assignee_id"], "full_name": task["assignee_name"]},
        "created_by": {"id": task["created_by"], "full_name": task["creator_name"]},
        "customer": {"id": task["customer_id"], "name": task["customer_name"]} if task["customer_id"] else None,
        "opportunity": ({"id": task["opportunity_id"], "name": task["opportunity_name"]}
                        if task["opportunity_id"] else None),
        "postpone_count": task["postpone_count"],
        "last_postpone_reason": task["last_postpone_reason"],
        "completed_at": clock.iso(task["completed_at"]),
        "completion_note": task["completion_note"],
        "source_activity_id": task["source_activity_id"],
        "created_at": clock.iso(task["created_at"]),
        "updated_at": clock.iso(task["updated_at"]),
    }


def _fetch(task_id: int) -> dict | None:
    return row(TASK_SELECT + " WHERE t.id = ?", (task_id,))


def get_visible_task(user: dict, task_id: int) -> dict:
    scope, params = task_scope(user)
    task = row(TASK_SELECT + f" WHERE t.id = ? AND {scope}", (task_id, *params))
    if task is None:
        raise NotFound("Không tìm thấy công việc hoặc bạn không có quyền với công việc này.")
    return task


def check_assignee(user: dict, assignee_id) -> dict:
    """Quy tắc giao việc: nhân viên tự giao cho mình, trưởng nhóm giao trong nhóm, giám đốc giao mọi người."""
    if assignee_id is None or assignee_id == user["id"]:
        return {"id": user["id"], "full_name": user["full_name"], "team_id": user.get("team_id")}
    if not at_least(user, "team_lead"):
        raise Forbidden("Nhân viên chỉ được tạo công việc cho chính mình. "
                        "Giao việc cho người khác là quyền của Trưởng nhóm.")
    assignee = get_active_user(assignee_id)
    if assignee is None:
        raise invalid("assignee_id", "Người thực hiện", "Người thực hiện không tồn tại hoặc đã ngừng hoạt động.")
    if user["role"] == "team_lead" and assignee["team_id"] != user.get("team_id"):
        raise Forbidden(f"Trưởng nhóm chỉ được giao việc cho thành viên trong nhóm của mình; "
                        f"{assignee['full_name']} không thuộc nhóm {user.get('team_name') or 'của bạn'}.")
    return assignee


def create_task(user: dict, payload: dict, *, source_activity_id: int | None = None) -> dict:
    data = validate(payload, CREATE_SCHEMA)
    today = clock.today()
    errors = []
    if data["due_date"] < today:
        errors.append(field_error("due_date", "Hạn hoàn thành",
                                  f"Hạn hoàn thành không được ở quá khứ (hôm nay là {format_date(today)})."))
    if data["customer_id"] is None and data["opportunity_id"] is None:
        errors.append(field_error("customer_id", "Khách hàng / Cơ hội",
                                  "Công việc phải gắn với một khách hàng hoặc một cơ hội."))
    if errors:
        raise ValidationFailed(errors)
    customer, _, opp = resolve_customer_links(user, data["customer_id"], None, data["opportunity_id"])
    assignee = check_assignee(user, data["assignee_id"])

    now_text = clock.to_db(clock.now())
    task_id = execute(
        "INSERT INTO tasks (title, description, due_date, priority, status, assignee_id, created_by, customer_id, "
        "opportunity_id, source_activity_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)",
        (data["title"], data["description"], data["due_date"].isoformat(), data["priority"], assignee["id"],
         user["id"], customer["id"], opp["id"] if opp else None, source_activity_id, now_text, now_text))
    who = "bạn" if assignee["id"] == user["id"] else assignee["full_name"]
    return {
        "message": (f"Đã tạo công việc \"{data['title']}\" cho {who}, hạn {format_date_weekday(data['due_date'])}, "
                    f"ưu tiên {TASK_PRIORITIES[data['priority']].lower()}."),
        "task": task_out(_fetch(task_id), today),
    }


def list_tasks(user: dict, args: dict) -> dict:
    params = validate(args, LIST_SCHEMA)
    today = clock.today()
    scope, values = task_scope(user)
    where = [scope]
    if params["status"] != "all":
        where.append("t.status = ?")
        values.append(params["status"])
    if params["assigned_to_me"]:
        where.append("t.assignee_id = ?")
        values.append(user["id"])
    for column in ("assignee_id", "customer_id", "opportunity_id", "priority"):
        if params[column] is not None:
            where.append(f"t.{column} = ?")
            values.append(params[column])
    if params["due"] == "overdue":
        where.append("t.status = 'open' AND t.due_date < ?")
        values.append(today.isoformat())
    elif params["due"] == "today":
        where.append("t.due_date = ?")
        values.append(today.isoformat())
    elif params["due"] == "next_7_days":
        where.append("t.due_date BETWEEN ? AND ?")
        values += [today.isoformat(), (today + timedelta(days=7)).isoformat()]
    if params["due_from"]:
        where.append("t.due_date >= ?")
        values.append(params["due_from"].isoformat())
    if params["due_to"]:
        where.append("t.due_date <= ?")
        values.append(params["due_to"].isoformat())
    if params["q"]:
        where.append("search_text(t.title) LIKE ?")
        values.append(f"%{search_text(params['q'])}%")
    condition = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM ({TASK_SELECT} WHERE {condition})", values)
    limit, offset = page_window(params)
    items = rows(TASK_SELECT + f" WHERE {condition} ORDER BY CASE t.status WHEN 'open' THEN 0 ELSE 1 END, "
                 f"t.due_date, {PRIORITY_ORDER}, t.id LIMIT ? OFFSET ?", [*values, limit, offset])
    return page_result([task_out(t, today) for t in items], total, params)


def get_task(user: dict, task_id: int) -> dict:
    task = task_out(get_visible_task(user, task_id))
    history = rows("SELECT p.*, u.full_name AS postponed_by_name FROM task_postponements p "
                   "JOIN users u ON u.id = p.postponed_by WHERE p.task_id = ? ORDER BY p.id", (task_id,))
    task["postponements"] = [{
        "old_due_date": h["old_due_date"],
        "new_due_date": h["new_due_date"],
        "reason": h["reason"],
        "postponed_by": {"id": h["postponed_by"], "full_name": h["postponed_by_name"]},
        "postponed_at": clock.iso(h["postponed_at"]),
    } for h in history]
    return task


def update_task(user: dict, task_id: int, payload: dict) -> dict:
    task = get_visible_task(user, task_id)
    data = validate(payload, UPDATE_SCHEMA, partial=True, forbidden=UPDATE_FORBIDDEN)
    if not data:
        raise invalid("body", "Dữ liệu", "Không có thông tin nào để cập nhật.")
    if task["status"] == "done":
        raise Conflict("Công việc đã hoàn thành, không thể chỉnh sửa. Hãy mở lại công việc nếu cần.")
    sets, values = [], []
    for key in ("title", "description", "priority"):
        if key in data:
            sets.append(f"{key} = ?")
            values.append(data[key])
    if "due_date" in data:
        old_due = date.fromisoformat(task["due_date"])
        new_due = data["due_date"]
        if new_due > old_due:
            raise invalid("due_date", "Hạn hoàn thành",
                          "Muốn lùi hạn, vui lòng dùng chức năng Hoãn công việc "
                          "(POST /api/tasks/{id}/postpone) và nhập lý do.")
        if new_due < clock.today():
            raise invalid("due_date", "Hạn hoàn thành", "Hạn hoàn thành không được ở quá khứ.")
        sets.append("due_date = ?")
        values.append(new_due.isoformat())
    if "customer_id" in data or "opportunity_id" in data:
        customer_id = data.get("customer_id", task["customer_id"])
        opportunity_id = data.get("opportunity_id", task["opportunity_id"])
        if "customer_id" in data and "opportunity_id" not in data and data["customer_id"] != task["customer_id"]:
            opportunity_id = None  # đổi khách hàng thì bỏ liên kết cơ hội cũ
        if "opportunity_id" in data and data["opportunity_id"] is not None and "customer_id" not in data:
            customer_id = None  # chỉ đổi cơ hội thì khách hàng lấy theo cơ hội mới
        if customer_id is None and opportunity_id is None:
            raise invalid("customer_id", "Khách hàng / Cơ hội", "Công việc phải gắn với một khách hàng hoặc một cơ hội.")
        customer, _, opp = resolve_customer_links(user, customer_id, None, opportunity_id)
        sets += ["customer_id = ?", "opportunity_id = ?"]
        values += [customer["id"], opp["id"] if opp else None]
    sets.append("updated_at = ?")
    values.append(clock.to_db(clock.now()))
    execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", (*values, task_id))
    updated = task_out(_fetch(task_id))
    return {"message": f"Đã cập nhật công việc \"{updated['title']}\".", "task": updated}
