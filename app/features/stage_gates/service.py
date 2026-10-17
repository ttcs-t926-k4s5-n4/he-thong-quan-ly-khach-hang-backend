"""SCRUM-90 – Điều kiện bắt buộc khi cơ hội rời một giai đoạn.

Tiêu chí:
- Không cho chuyển giai đoạn nếu chưa thoả điều kiện đã cấu hình (ví dụ chưa có cuộc gặp nào được ghi nhận).
- Thông báo nêu rõ còn thiếu điều kiện gì.
- Trưởng nhóm trở lên có thể ghi đè kèm lý do (được lưu vết trong lịch sử chuyển giai đoạn).

Quy tắc áp dụng:
- Điều kiện gắn với giai đoạn bị RỜI ĐI. Khi chuyển tiến nhảy cóc (VD: 1 -> 4) thì điều kiện của
  mọi giai đoạn bị bỏ qua (1, 2, 3) đều phải thoả, tránh "đẩy giai đoạn cho đẹp báo cáo".
- Điều kiện only_forward = true (mặc định) chỉ áp dụng khi chuyển tiến; chuyển lùi hoặc chuyển
  sang "Thua" không bị chặn bởi các điều kiện này.
- Tạo mới cơ hội ở giai đoạn sau giai đoạn đầu tiên cũng phải thoả điều kiện như khi chuyển tiến.
"""
from __future__ import annotations

import json

from app import clock
from app.common.access import get_visible_opportunity, serialize_opportunity
from app.common.stages import get_stage, is_closed, list_stages, stage_out
from app.db import execute, row, rows, scalar
from app.errors import Conflict, Forbidden, NotFound
from app.labels import ACTIVITY_TYPES, RULE_FIELDS, RULE_TYPES, format_vnd
from app.permissions import at_least, owner_scope, require_role
from app.validation import (PAGINATION, Bool, Choice, DateField, Int, Str, field_error, invalid,
                            page_result, page_window, validate)
from app.errors import ValidationFailed

OVERRIDE_MIN_REASON = 10
OVERRIDE_HINT = ("Trưởng nhóm trở lên có thể ghi đè bằng cách gửi thêm \"override\": true và "
                 f"\"override_reason\" (ít nhất {OVERRIDE_MIN_REASON} ký tự).")

CHANGE_STAGE_SCHEMA = {
    "to_stage_id": Int("Giai đoạn mới", required=True, min_value=1),
    "override": Bool("Ghi đè điều kiện", default=False),
    "override_reason": Str("Lý do ghi đè", max_len=1000),
}

RULE_SCHEMA = {
    "stage_id": Int("Giai đoạn", required=True, min_value=1),
    "rule_type": Choice("Loại điều kiện", RULE_TYPES, required=True),
    "activity_type": Choice("Loại hoạt động", ACTIVITY_TYPES),
    "min_count": Int("Số lượng tối thiểu", min_value=1, max_value=100),
    "field_name": Choice("Thông tin bắt buộc", RULE_FIELDS),
    "min_amount": Int("Giá trị tối thiểu", min_value=1, max_value=10**15),
    "only_forward": Bool("Chỉ áp dụng khi chuyển tiến", default=True),
    "custom_message": Str("Thông báo tuỳ chỉnh", max_len=500),
    "is_active": Bool("Đang áp dụng", default=True),
}

CONFIG_DENIED = ("Chỉ Giám đốc kinh doanh hoặc Quản trị hệ thống mới được cấu hình "
                 "điều kiện chuyển giai đoạn.")


# ============================================================ Đánh giá điều kiện

def count_completed_activities(opp_id, activity_type=None) -> int:
    if opp_id is None:
        return 0
    sql = ("SELECT COUNT(*) FROM activities WHERE opportunity_id = ? AND status = 'completed' "
           "AND occurred_at <= ?")
    params = [opp_id, clock.to_db(clock.now())]
    if activity_type:
        sql += " AND activity_type = ?"
        params.append(activity_type)
    return scalar(sql, params) or 0


def count_product_lines(opp_id) -> int:
    if opp_id is None:
        return 0
    return scalar("SELECT COUNT(*) FROM opportunity_lines WHERE opportunity_id = ?", (opp_id,)) or 0


def check_rule(rule: dict, opp: dict) -> tuple[bool, str, str | None]:
    """Kiểm tra một điều kiện. Trả về (đạt?, thông báo khi chưa đạt, tình trạng hiện tại)."""
    rule_type = rule["rule_type"]
    if rule_type == "min_activities":
        need = rule["min_count"] or 1
        have = count_completed_activities(opp.get("id"), rule["activity_type"])
        kind = ACTIVITY_TYPES[rule["activity_type"]].lower() if rule["activity_type"] else "hoạt động"
        return have >= need, f"Cần ít nhất {need} {kind} đã diễn ra được ghi nhận cho cơ hội", f"hiện có {have}"
    if rule_type == "required_field":
        label = RULE_FIELDS.get(rule["field_name"], rule["field_name"])
        value = opp.get(rule["field_name"])
        filled = value is not None and str(value).strip() != ""
        return filled, f"Chưa có {label.lower()} cho cơ hội", None
    if rule_type == "min_product_lines":
        need = rule["min_count"] or 1
        have = count_product_lines(opp.get("id"))
        return have >= need, f"Cần ít nhất {need} dòng sản phẩm/dịch vụ trong cơ hội", f"hiện có {have}"
    if rule_type == "min_amount":
        need = rule["min_amount"] or 0
        have = opp.get("amount") or 0
        return have >= need, f"Giá trị cơ hội phải từ {format_vnd(need)} trở lên", f"hiện tại {format_vnd(have)}"
    return True, "", None


def evaluate_transition(opp: dict, from_stage: dict, to_stage: dict) -> list[dict]:
    """Danh sách điều kiện CHƯA thoả khi chuyển cơ hội từ from_stage sang to_stage."""
    forward = (not to_stage["is_lost"]) and to_stage["sort_order"] > from_stage["sort_order"]
    if forward:
        stage_ids = [s["id"] for s in list_stages()
                     if from_stage["sort_order"] <= s["sort_order"] < to_stage["sort_order"] and not is_closed(s)]
    else:
        stage_ids = [from_stage["id"]]
    if not stage_ids:
        return []
    marks = ",".join("?" * len(stage_ids))
    rules = rows("SELECT r.*, s.name AS stage_name FROM stage_exit_rules r "
                 "JOIN pipeline_stages s ON s.id = r.stage_id "
                 f"WHERE r.is_active = 1 AND r.stage_id IN ({marks}) ORDER BY s.sort_order, r.id", stage_ids)
    unmet = []
    for rule in rules:
        if not forward and rule["only_forward"]:
            continue
        passed, message, current = check_rule(rule, opp)
        if passed:
            continue
        text = rule["custom_message"] or message
        unmet.append({
            "rule_id": rule["id"],
            "stage_id": rule["stage_id"],
            "stage_name": rule["stage_name"],
            "rule_type": rule["rule_type"],
            "rule_type_label": RULE_TYPES[rule["rule_type"]],
            "message": f"{text} ({current})." if current else f"{text}.",
        })
    return unmet


def blocked_message(opp_name: str, to_stage: dict, unmet: list[dict]) -> str:
    details = " ".join(f"({i}) Rời giai đoạn \"{u['stage_name']}\": {u['message']}"
                       for i, u in enumerate(unmet, 1))
    return (f"Chưa thể chuyển cơ hội \"{opp_name}\" sang giai đoạn \"{to_stage['name']}\" "
            f"vì còn thiếu {len(unmet)} điều kiện: {details}")


def enforce(user: dict, opp_name: str, to_stage: dict, unmet: list[dict],
            override: bool, override_reason: str | None) -> bool:
    """Chặn nếu còn điều kiện chưa thoả; cho phép trưởng nhóm trở lên ghi đè kèm lý do.

    Trả về True nếu đã ghi đè.
    """
    if not unmet:
        return False
    can_override = at_least(user, "team_lead")
    if not override:
        raise Conflict(blocked_message(opp_name, to_stage, unmet), code="STAGE_CONDITIONS_UNMET", extra={
            "missing_conditions": unmet,
            "can_override": can_override,
            "override_hint": OVERRIDE_HINT if can_override else
            "Bạn cần bổ sung các điều kiện trên hoặc nhờ Trưởng nhóm ghi đè.",
        })
    if not can_override:
        raise Forbidden("Chỉ Trưởng nhóm trở lên mới được ghi đè điều kiện chuyển giai đoạn.",
                        extra={"missing_conditions": unmet})
    if not override_reason or len(override_reason.strip()) < OVERRIDE_MIN_REASON:
        raise invalid("override_reason", "Lý do ghi đè",
                      f"Vui lòng nhập lý do ghi đè (ít nhất {OVERRIDE_MIN_REASON} ký tự).")
    return True


def record_history(opp_id: int, from_stage_id, to_stage_id: int, user_id: int,
                   is_override: bool, reason: str | None, unmet: list[dict] | None) -> int:
    return execute(
        "INSERT INTO opportunity_stage_history (opportunity_id, from_stage_id, to_stage_id, changed_by, "
        "changed_at, is_override, override_reason, unmet_conditions) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (opp_id, from_stage_id, to_stage_id, user_id, clock.to_db(clock.now()), int(is_override),
         reason if is_override else None,
         json.dumps(unmet, ensure_ascii=False) if is_override and unmet else None),
    )


# ============================================================ Chuyển giai đoạn

def _load_target_stage(stage_id: int) -> dict:
    stage = get_stage(stage_id)
    if stage is None or not stage["is_active"]:
        raise invalid("to_stage_id", "Giai đoạn mới", "Giai đoạn không tồn tại hoặc đã ngừng sử dụng.")
    return stage


def change_stage(user: dict, opp_id: int, payload: dict, *, allow_same: bool = False) -> dict:
    """Chuyển giai đoạn cơ hội (dùng chung cho API chuyển giai đoạn và kéo thả trên kanban)."""
    data = validate(payload, CHANGE_STAGE_SCHEMA)
    opp = get_visible_opportunity(user, opp_id)
    to_stage = _load_target_stage(data["to_stage_id"])
    from_stage = get_stage(opp["stage_id"])

    if to_stage["id"] == from_stage["id"]:
        if allow_same:
            return {"changed": False, "override_applied": False,
                    "message": f"Cơ hội \"{opp['name']}\" vẫn ở giai đoạn \"{from_stage['name']}\".",
                    "opportunity": serialize_opportunity(opp)}
        raise Conflict(f"Cơ hội \"{opp['name']}\" đang ở giai đoạn \"{from_stage['name']}\" rồi.")

    unmet = evaluate_transition(opp, from_stage, to_stage)
    overridden = enforce(user, opp["name"], to_stage, unmet, data["override"], data["override_reason"])

    now_text = clock.to_db(clock.now())
    execute("UPDATE opportunities SET stage_id = ?, probability = ?, probability_is_manual = 0, "
            "probability_note = NULL, stage_entered_at = ?, closed_at = ?, updated_at = ? WHERE id = ?",
            (to_stage["id"], to_stage["default_probability"], now_text,
             now_text if is_closed(to_stage) else None, now_text, opp_id))
    record_history(opp_id, from_stage["id"], to_stage["id"], user["id"], overridden,
                   data["override_reason"], unmet)

    message = (f"Đã chuyển cơ hội \"{opp['name']}\" từ giai đoạn \"{from_stage['name']}\" "
               f"sang \"{to_stage['name']}\". Xác suất thắng: {to_stage['default_probability']}%.")
    if overridden:
        message += (f" Đã ghi đè {len(unmet)} điều kiện chưa thoả với lý do: "
                    f"{data['override_reason'].strip()}")
    return {
        "changed": True,
        "override_applied": overridden,
        "overridden_conditions": unmet if overridden else [],
        "message": message,
        "opportunity": serialize_opportunity(get_visible_opportunity(user, opp_id)),
    }


def _next_stage(current: dict) -> dict | None:
    for stage in list_stages():
        if stage["sort_order"] > current["sort_order"] and not stage["is_lost"]:
            return stage
    return None


def stage_check(user: dict, opp_id: int, args: dict) -> dict:
    """Kiểm tra trước (không chuyển) xem cơ hội đã đủ điều kiện sang giai đoạn đích chưa."""
    params = validate(args, {"to_stage_id": Int("Giai đoạn đích", min_value=1)})
    opp = get_visible_opportunity(user, opp_id)
    from_stage = get_stage(opp["stage_id"])
    if params["to_stage_id"] is not None:
        to_stage = _load_target_stage(params["to_stage_id"])
    else:
        to_stage = _next_stage(from_stage)
        if to_stage is None:
            raise invalid("to_stage_id", "Giai đoạn đích",
                          "Cơ hội không còn giai đoạn kế tiếp, vui lòng chọn giai đoạn đích (to_stage_id).")
    if to_stage["id"] == from_stage["id"]:
        unmet, message = [], f"Cơ hội đang ở giai đoạn \"{from_stage['name']}\"."
    else:
        unmet = evaluate_transition(opp, from_stage, to_stage)
        message = (blocked_message(opp["name"], to_stage, unmet) if unmet else
                   f"Cơ hội đã đủ điều kiện để chuyển sang giai đoạn \"{to_stage['name']}\".")
    return {
        "opportunity_id": opp["id"],
        "from_stage": stage_out(from_stage),
        "to_stage": stage_out(to_stage),
        "can_move": not unmet and to_stage["id"] != from_stage["id"],
        "missing_conditions": unmet,
        "can_override": bool(unmet) and at_least(user, "team_lead"),
        "message": message,
    }


# ============================================================ Lịch sử & nhật ký ghi đè

HISTORY_SELECT = """
SELECT h.*, fs.name AS from_stage_name, ts.name AS to_stage_name, u.full_name AS changed_by_name,
       o.name AS opportunity_name, c.name AS customer_name
FROM opportunity_stage_history h
JOIN opportunities o ON o.id = h.opportunity_id
JOIN customers c ON c.id = o.customer_id
LEFT JOIN pipeline_stages fs ON fs.id = h.from_stage_id
JOIN pipeline_stages ts ON ts.id = h.to_stage_id
JOIN users u ON u.id = h.changed_by
"""


def _history_out(h: dict, with_opportunity: bool = False) -> dict:
    item = {
        "id": h["id"],
        "from_stage": {"id": h["from_stage_id"], "name": h["from_stage_name"]} if h["from_stage_id"] else None,
        "to_stage": {"id": h["to_stage_id"], "name": h["to_stage_name"]},
        "changed_by": {"id": h["changed_by"], "full_name": h["changed_by_name"]},
        "changed_at": clock.iso(h["changed_at"]),
        "is_override": bool(h["is_override"]),
        "override_reason": h["override_reason"],
        "unmet_conditions": json.loads(h["unmet_conditions"]) if h["unmet_conditions"] else [],
        "description": (f"Tạo mới ở giai đoạn \"{h['to_stage_name']}\"" if not h["from_stage_id"] else
                        f"Chuyển từ \"{h['from_stage_name']}\" sang \"{h['to_stage_name']}\"")
                       + (" (có ghi đè điều kiện)" if h["is_override"] else ""),
    }
    if with_opportunity:
        item["opportunity"] = {"id": h["opportunity_id"], "name": h["opportunity_name"],
                               "customer_name": h["customer_name"]}
    return item


def stage_history(user: dict, opp_id: int) -> dict:
    opp = get_visible_opportunity(user, opp_id)
    items = rows(HISTORY_SELECT + " WHERE h.opportunity_id = ? ORDER BY h.changed_at, h.id", (opp_id,))
    return {"opportunity": {"id": opp["id"], "name": opp["name"]}, "items": [_history_out(h) for h in items]}


def override_log(user: dict, args: dict) -> dict:
    require_role(user, "team_lead", "Chỉ Trưởng nhóm trở lên mới xem được nhật ký ghi đè điều kiện.")
    params = validate(args, {"date_from": DateField("Từ ngày"), "date_to": DateField("Đến ngày"), **PAGINATION})
    scope, scope_params = owner_scope(user, "o.owner_id")
    where, values = [f"h.is_override = 1", scope], list(scope_params)
    if params["date_from"]:
        where.append("h.changed_at >= ?")
        values.append(f"{params['date_from'].isoformat()} 00:00:00")
    if params["date_to"]:
        where.append("h.changed_at <= ?")
        values.append(f"{params['date_to'].isoformat()} 23:59:59")
    condition = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM ({HISTORY_SELECT} WHERE {condition})", values)
    limit, offset = page_window(params)
    items = rows(HISTORY_SELECT + f" WHERE {condition} ORDER BY h.changed_at DESC, h.id DESC LIMIT ? OFFSET ?",
                 [*values, limit, offset])
    return page_result([_history_out(h, with_opportunity=True) for h in items], total, params)


# ============================================================ Cấu hình điều kiện (Giám đốc kinh doanh)

def rule_summary(rule: dict, stage_name: str) -> str:
    rule_type = rule["rule_type"]
    if rule_type == "min_activities":
        kind = ACTIVITY_TYPES[rule["activity_type"]].lower() if rule["activity_type"] else "hoạt động"
        need = f"cần ít nhất {rule['min_count']} {kind} đã diễn ra"
    elif rule_type == "required_field":
        need = f"bắt buộc có {RULE_FIELDS.get(rule['field_name'], rule['field_name']).lower()}"
    elif rule_type == "min_product_lines":
        need = f"cần ít nhất {rule['min_count']} dòng sản phẩm/dịch vụ"
    else:
        need = f"giá trị cơ hội tối thiểu {format_vnd(rule['min_amount'])}"
    scope = "khi chuyển tiến" if rule["only_forward"] else "khi chuyển sang bất kỳ giai đoạn nào"
    return f"Khi rời giai đoạn \"{stage_name}\" ({scope}): {need}."


def rule_out(rule: dict) -> dict:
    stage = get_stage(rule["stage_id"])
    return {
        "id": rule["id"],
        "stage": {"id": stage["id"], "name": stage["name"]},
        "rule_type": rule["rule_type"],
        "rule_type_label": RULE_TYPES[rule["rule_type"]],
        "activity_type": rule["activity_type"],
        "activity_type_label": ACTIVITY_TYPES.get(rule["activity_type"]) if rule["activity_type"] else None,
        "min_count": rule["min_count"],
        "field_name": rule["field_name"],
        "field_label": RULE_FIELDS.get(rule["field_name"]) if rule["field_name"] else None,
        "min_amount": rule["min_amount"],
