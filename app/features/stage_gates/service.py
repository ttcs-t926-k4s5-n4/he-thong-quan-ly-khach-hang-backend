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
