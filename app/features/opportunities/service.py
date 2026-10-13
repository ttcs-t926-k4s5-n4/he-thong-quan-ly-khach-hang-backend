"""SCRUM-87 – Tạo và quản lý cơ hội bán hàng.

Tiêu chí:
- Khai báo tên cơ hội, khách hàng, người liên hệ chính, giai đoạn, giá trị dự kiến, ngày dự kiến chốt, nguồn.
- Xác suất thắng lấy mặc định theo giai đoạn, sửa tay được kèm ghi chú.
- Một khách hàng có thể có nhiều cơ hội song song.
- Ngày dự kiến chốt không được ở quá khứ khi tạo mới.
"""
from __future__ import annotations

from app import clock
from app.common.access import (OPP_SELECT, get_active_user, get_contact, get_visible_customer,
                               get_visible_opportunity, serialize_opportunity)
from app.common.stages import first_open_stage, get_stage, is_closed
from app.db import execute, rows, scalar
from app.errors import Conflict, Forbidden, ValidationFailed
from app.features.stage_gates import service as gates
from app.labels import OPPORTUNITY_SOURCES, OPPORTUNITY_STATUSES, format_date, search_text
from app.permissions import at_least, can_access_owner, owner_scope
from app.validation import (PAGINATION, Bool, Choice, DateField, Int, Str, field_error, invalid,
                            page_result, page_window, validate)

MAX_MONEY = 10**15

CREATE_SCHEMA = {
    "name": Str("Tên cơ hội", required=True, min_len=1, max_len=255),
    "customer_id": Int("Khách hàng", required=True, min_value=1),
    "primary_contact_id": Int("Người liên hệ chính", min_value=1),
    "stage_id": Int("Giai đoạn", min_value=1),
    "estimated_value": Int("Giá trị dự kiến", min_value=0, max_value=MAX_MONEY, default=0),
    "expected_close_date": DateField("Ngày dự kiến chốt", required=True),
    "source": Choice("Nguồn cơ hội", OPPORTUNITY_SOURCES, default="other"),
    "description": Str("Mô tả nhu cầu", max_len=4000),
    "probability": Int("Xác suất thắng (%)", min_value=0, max_value=100),
    "probability_note": Str("Ghi chú xác suất", max_len=500),
    "owner_id": Int("Người phụ trách", min_value=1),
    "override": Bool("Ghi đè điều kiện", default=False),
    "override_reason": Str("Lý do ghi đè", max_len=1000),
}

UPDATE_SCHEMA = {
    "name": Str("Tên cơ hội", required=True, min_len=1, max_len=255),
    "primary_contact_id": Int("Người liên hệ chính", min_value=1),
    "estimated_value": Int("Giá trị dự kiến", min_value=0, max_value=MAX_MONEY, nullable=False),
    "expected_close_date": DateField("Ngày dự kiến chốt", nullable=False),
    "source": Choice("Nguồn cơ hội", OPPORTUNITY_SOURCES, nullable=False),
    "description": Str("Mô tả nhu cầu", max_len=4000),
    "probability": Int("Xác suất thắng (%)", min_value=0, max_value=100, nullable=False),
    "probability_note": Str("Ghi chú xác suất", max_len=500),
    "owner_id": Int("Người phụ trách", min_value=1, nullable=False),
}

UPDATE_FORBIDDEN = {
    "stage_id": "Không đổi giai đoạn ở đây. Vui lòng dùng chức năng chuyển giai đoạn "
                "(POST /api/opportunities/{id}/change-stage hoặc kéo thả trên bảng pipeline).",
    "customer_id": "Không thể đổi khách hàng của cơ hội. Hãy tạo cơ hội mới cho khách hàng khác.",
    "amount": "Giá trị cơ hội được tính tự động: sửa \"estimated_value\" (khi chưa có dòng sản phẩm) "
              "hoặc sửa các dòng sản phẩm.",
}

LIST_SCHEMA = {
    "customer_id": Int("Khách hàng", min_value=1),
    "stage_id": Int("Giai đoạn", min_value=1),
    "owner_id": Int("Người phụ trách", min_value=1),
    "status": Choice("Trạng thái", {**OPPORTUNITY_STATUSES, "all": "Tất cả"}, default="all"),
    "q": Str("Từ khoá", max_len=100),
    "close_from": DateField("Ngày chốt từ"),
    "close_to": DateField("Ngày chốt đến"),
    **PAGINATION,
}


def _resolve_owner(user: dict, owner_id) -> dict:
    """Người phụ trách: mặc định là người tạo; trưởng nhóm trở lên được giao cho người khác trong phạm vi."""
    if owner_id is None or owner_id == user["id"]:
        return user
    if not at_least(user, "team_lead"):
        raise Forbidden("Nhân viên chỉ được tạo và phụ trách cơ hội của chính mình. "
                        "Việc giao cơ hội cho người khác do Trưởng nhóm trở lên thực hiện.")
    owner = get_active_user(owner_id)
    if owner is None:
        raise invalid("owner_id", "Người phụ trách", "Người phụ trách không tồn tại hoặc đã ngừng hoạt động.")
    if not can_access_owner(user, owner):
        raise Forbidden("Bạn chỉ được giao cơ hội cho thành viên trong nhóm của mình.")
    return owner


def _resolve_probability(stage: dict, probability, note, errors: list) -> tuple[int, bool, str | None]:
    """Xác suất mặc định theo giai đoạn; sửa tay (khác mặc định) bắt buộc kèm ghi chú."""
    default = stage["default_probability"]
    if probability is None or probability == default:
        return default, False, None
    if not note:
        errors.append(field_error(
            "probability_note", "Ghi chú xác suất",
            f"Vui lòng nhập ghi chú khi sửa tay xác suất thắng thành {probability}% "
            f"(mặc định của giai đoạn \"{stage['name']}\" là {default}%)."))
        return default, False, None
    return probability, True, note


def create_opportunity(user: dict, payload: dict) -> dict:
    data = validate(payload, CREATE_SCHEMA)
    errors = []
    today = clock.today()
    if data["expected_close_date"] < today:
        errors.append(field_error("expected_close_date", "Ngày dự kiến chốt",
                                  f"Ngày dự kiến chốt không được ở quá khứ (hôm nay là {format_date(today)})."))

    customer = get_visible_customer(user, data["customer_id"])
    if customer is None:
        errors.append(field_error("customer_id", "Khách hàng",
                                  "Khách hàng không tồn tại hoặc bạn không có quyền với khách hàng này."))
    elif data["primary_contact_id"] is not None:
        contact = get_contact(data["primary_contact_id"])
        if contact is None or contact["customer_id"] != customer["id"]:
            errors.append(field_error("primary_contact_id", "Người liên hệ chính",
                                      "Người liên hệ chính không thuộc khách hàng đã chọn."))

    first_stage = first_open_stage()
    stage = first_stage
    if data["stage_id"] is not None:
        stage = get_stage(data["stage_id"])
        if stage is None or not stage["is_active"]:
            errors.append(field_error("stage_id", "Giai đoạn", "Giai đoạn không tồn tại."))
            stage = None
        elif is_closed(stage):
            errors.append(field_error("stage_id", "Giai đoạn",
                                      "Không thể tạo mới cơ hội ở giai đoạn đã đóng (Thắng/Thua)."))
            stage = None

    probability, manual, note = (0, False, None)
    if stage is not None:
        probability, manual, note = _resolve_probability(stage, data["probability"],
                                                         data["probability_note"], errors)
    if errors:
        raise ValidationFailed(errors)

    owner = _resolve_owner(user, data["owner_id"])

    # SCRUM-90: tạo thẳng ở giai đoạn sau cũng phải thoả điều kiện của các giai đoạn trước đó
    unmet, overridden = [], False
    if stage["id"] != first_stage["id"]:
        snapshot = {"id": None, "primary_contact_id": data["primary_contact_id"],
                    "description": data["description"], "amount": data["estimated_value"]}
        unmet = gates.evaluate_transition(snapshot, first_stage, stage)
        overridden = gates.enforce(user, data["name"], stage, unmet, data["override"], data["override_reason"])

    now_text = clock.to_db(clock.now())
    opp_id = execute(
        "INSERT INTO opportunities (name, customer_id, primary_contact_id, stage_id, estimated_value, amount, "
        "amount_source, recurring_annual_value, expected_close_date, source, description, probability, "
        "probability_is_manual, probability_note, owner_id, stage_entered_at, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 'manual', 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data["name"], customer["id"], data["primary_contact_id"], stage["id"], data["estimated_value"],
         data["estimated_value"], data["expected_close_date"].isoformat(), data["source"], data["description"],
         probability, int(manual), note, owner["id"], now_text, user["id"], now_text, now_text))
    gates.record_history(opp_id, None, stage["id"], user["id"], overridden, data["override_reason"], unmet)

    opportunity = serialize_opportunity(get_visible_opportunity(user, opp_id))
    open_count = scalar("SELECT COUNT(*) FROM opportunities o JOIN pipeline_stages s ON s.id = o.stage_id "
                        "WHERE o.customer_id = ? AND o.is_deleted = 0 AND s.is_won = 0 AND s.is_lost = 0",
                        (customer["id"],))
    message = f"Đã tạo cơ hội \"{data['name']}\" cho khách hàng {customer['name']}."
    if open_count > 1:
        message += f" Khách hàng này hiện có {open_count} cơ hội đang mở."
    if overridden:
        message += f" Đã ghi đè {len(unmet)} điều kiện giai đoạn với lý do: {data['override_reason']}"
    return {"message": message, "opportunity": opportunity}


def list_opportunities(user: dict, args: dict) -> dict:
    params = validate(args, LIST_SCHEMA)
    scope, values = owner_scope(user, "o.owner_id")
    where = ["o.is_deleted = 0", scope]
    for column in ("customer_id", "stage_id", "owner_id"):
        if params[column] is not None:
            where.append(f"o.{column} = ?")
            values.append(params[column])
    status = params["status"]
    if status == "open":
        where.append("s.is_won = 0 AND s.is_lost = 0")
    elif status == "won":
        where.append("s.is_won = 1")
    elif status == "lost":
        where.append("s.is_lost = 1")
    if params["q"]:
        where.append("(search_text(o.name) LIKE ? OR search_text(c.name) LIKE ?)")
        keyword = f"%{search_text(params['q'])}%"
        values += [keyword, keyword]
    if params["close_from"]:
        where.append("o.expected_close_date >= ?")
        values.append(params["close_from"].isoformat())
    if params["close_to"]:
        where.append("o.expected_close_date <= ?")
        values.append(params["close_to"].isoformat())
    condition = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM ({OPP_SELECT} WHERE {condition})", values)
    limit, offset = page_window(params)
    items = rows(OPP_SELECT + f" WHERE {condition} ORDER BY o.updated_at DESC, o.id DESC LIMIT ? OFFSET ?",
                 [*values, limit, offset])
    return page_result([serialize_opportunity(r) for r in items], total, params)
