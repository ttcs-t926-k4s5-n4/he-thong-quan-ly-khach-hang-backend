"""SCRUM-88 – Điều hành cơ hội trên bảng pipeline dạng kanban.

Tiêu chí:
- Mỗi cột là một giai đoạn, hiển thị số cơ hội và tổng giá trị của cột.
- Kéo thả để chuyển giai đoạn (dùng chung logic chuyển giai đoạn + điều kiện của SCRUM-90).
- Thẻ cơ hội hiển thị tên khách, giá trị, ngày dự kiến chốt và cảnh báo nếu đình trệ.
- Lọc theo người sở hữu, nhóm, khoảng ngày chốt; nhân viên mặc định chỉ thấy cơ hội của mình.

Cảnh báo trên thẻ (chỉ với cơ hội đang mở):
- Đình trệ: nằm ở giai đoạn hiện tại lâu hơn ngưỡng của giai đoạn (stale_after_days), hoặc
  không có hoạt động nào được ghi nhận trong số ngày bằng ngưỡng đó.
- Quá hạn: đã qua ngày dự kiến chốt mà chưa chốt.
"""
from __future__ import annotations

from datetime import date

from app import clock
from app.common.access import get_any_user
from app.common.stages import is_closed, list_stages, stage_out
from app.db import row, rows
from app.errors import Forbidden
from app.features.stage_gates import service as gates
from app.labels import format_date, round_vnd, search_text
from app.permissions import can_access_owner, owner_scope, sees_everything
from app.validation import Bool, DateField, Int, Str, invalid, validate

BOARD_SCHEMA = {
    "owner_id": Int("Người sở hữu", min_value=1),
    "team_id": Int("Nhóm", min_value=1),
    "close_from": DateField("Ngày chốt từ"),
    "close_to": DateField("Ngày chốt đến"),
    "include_closed": Bool("Hiển thị cột Thắng/Thua", default=True),
    "q": Str("Từ khoá", max_len=100),
}

CARD_SELECT = """
SELECT o.id, o.name, o.amount, o.probability, o.expected_close_date, o.stage_id, o.stage_entered_at,
       o.created_at, o.customer_id, c.name AS customer_name, o.owner_id, u.full_name AS owner_name,
       (SELECT MAX(a.occurred_at) FROM activities a
         WHERE a.opportunity_id = o.id AND a.status = 'completed') AS last_activity_at
FROM opportunities o
JOIN customers c ON c.id = o.customer_id
JOIN users u ON u.id = o.owner_id
JOIN pipeline_stages s ON s.id = o.stage_id
"""


def _filters(user: dict, params: dict) -> tuple[str, list, str]:
    """Điều kiện SQL theo phạm vi quyền + bộ lọc. Trả về (điều kiện, tham số, nhãn phạm vi)."""
    scope, values = owner_scope(user, "o.owner_id")
    where = ["o.is_deleted = 0", scope]
    if sees_everything(user):
        label = "Toàn bộ cơ hội của công ty"
    elif user["role"] == "team_lead":
        label = f"Cơ hội của nhóm {user.get('team_name') or ''}".strip()
    else:
        label = "Cơ hội của tôi"

    if params.get("owner_id") is not None:
        owner = get_any_user(params["owner_id"])
        if owner is None:
            raise invalid("owner_id", "Người sở hữu", "Người sở hữu không tồn tại.")
        if not can_access_owner(user, owner):
            if user["role"] == "staff":
                raise Forbidden("Nhân viên chỉ được xem cơ hội của chính mình.")
            raise Forbidden("Bạn chỉ được xem cơ hội của thành viên trong nhóm mình.")
        where.append("o.owner_id = ?")
        values.append(owner["id"])
        label = f"Cơ hội của {owner['full_name']}"
    if params.get("team_id") is not None:
        team = row("SELECT * FROM teams WHERE id = ?", (params["team_id"],))
        if team is None:
            raise invalid("team_id", "Nhóm", "Nhóm không tồn tại.")
        if not sees_everything(user) and team["id"] != user.get("team_id"):
            raise Forbidden("Bạn chỉ được xem cơ hội trong nhóm của mình.")
        where.append("u.team_id = ?")
        values.append(team["id"])
        if params.get("owner_id") is None and (sees_everything(user) or user["role"] == "team_lead"):
            label = f"Cơ hội của nhóm {team['name']}"
    close_from, close_to = params.get("close_from"), params.get("close_to")
    if close_from and close_to and close_from > close_to:
        raise invalid("close_to", "Ngày chốt đến", "Ngày chốt đến phải bằng hoặc sau ngày chốt từ.")
    if close_from:
        where.append("o.expected_close_date >= ?")
        values.append(close_from.isoformat())
    if close_to:
        where.append("o.expected_close_date <= ?")
        values.append(close_to.isoformat())
    if params.get("q"):
        where.append("(search_text(o.name) LIKE ? OR search_text(c.name) LIKE ?)")
        keyword = f"%{search_text(params['q'])}%"
        values += [keyword, keyword]
    if params.get("include_closed") is False:
        where.append("s.is_won = 0 AND s.is_lost = 0")
    return " AND ".join(where), values, label


def _card(record: dict, stage: dict, today: date) -> dict:
    days_in_stage = (today - clock.from_db(record["stage_entered_at"]).date()).days
    last_activity = clock.from_db(record["last_activity_at"])
    close_date = date.fromisoformat(record["expected_close_date"])
    warnings, is_stale, is_overdue = [], False, False
    if not is_closed(stage):
        threshold = stage["stale_after_days"]
        if threshold:
            if days_in_stage > threshold:
                is_stale = True
                warnings.append(f"Đình trệ: đã nằm ở giai đoạn \"{stage['name']}\" {days_in_stage} ngày "
                                f"(ngưỡng {threshold} ngày).")
            reference = last_activity or clock.from_db(record["created_at"])
            idle_days = (today - reference.date()).days
            if idle_days > threshold:
                is_stale = True
                if last_activity:
                    warnings.append(f"Không có hoạt động nào trong {idle_days} ngày gần đây "
                                    f"(lần cuối {format_date(last_activity)}).")
                else:
                    warnings.append(f"Chưa có hoạt động nào được ghi nhận kể từ khi tạo cơ hội ({idle_days} ngày).")
        if close_date < today:
            is_overdue = True
            warnings.append(f"Đã quá ngày dự kiến chốt {(today - close_date).days} ngày "
                            f"({format_date(close_date)}).")
    return {
        "id": record["id"],
        "name": record["name"],
        "customer": {"id": record["customer_id"], "name": record["customer_name"]},
        "customer_name": record["customer_name"],
        "amount": record["amount"],
        "probability": record["probability"],
        "weighted_amount": round_vnd(record["amount"] * record["probability"] / 100),
        "expected_close_date": record["expected_close_date"],
        "owner": {"id": record["owner_id"], "full_name": record["owner_name"]},
        "stage_id": record["stage_id"],
        "days_in_stage": days_in_stage,
        "last_activity_at": clock.iso(record["last_activity_at"]),
        "is_stale": is_stale,
        "is_overdue": is_overdue,
        "warning_level": "danger" if is_overdue else ("warning" if is_stale else "none"),
        "warnings": warnings,
    }


def _column_totals(cards: list[dict]) -> dict:
    return {
        "count": len(cards),
        "total_amount": sum(c["amount"] for c in cards),
        "weighted_amount": sum(c["weighted_amount"] for c in cards),
        "stale_count": sum(1 for c in cards if c["is_stale"]),
        "overdue_count": sum(1 for c in cards if c["is_overdue"]),
    }


def get_board(user: dict, args: dict) -> dict:
    params = validate(args, BOARD_SCHEMA)
    condition, values, label = _filters(user, params)
    records = rows(CARD_SELECT + f" WHERE {condition} ORDER BY o.expected_close_date, o.id", values)
    stages = [s for s in list_stages() if params["include_closed"] or not is_closed(s)]
    today = clock.today()
    by_stage = {s["id"]: [] for s in stages}
    stage_map = {s["id"]: s for s in stages}
    for record in records:
        if record["stage_id"] in by_stage:
            by_stage[record["stage_id"]].append(_card(record, stage_map[record["stage_id"]], today))
    columns = []
    for stage in stages:
        cards = by_stage[stage["id"]]
        columns.append({"stage": stage_out(stage), **_column_totals(cards), "cards": cards})
    all_cards = [card for column in columns for card in column["cards"]]
    open_cards = [card for column in columns if not column["stage"]["is_closed"] for card in column["cards"]]
    return {
        "scope_label": label,
        "filters": {key: (value.isoformat() if isinstance(value, date) else value) for key, value in params.items()},
        "summary": {
            **_column_totals(all_cards),
            "open_count": len(open_cards),
            "open_amount": sum(c["amount"] for c in open_cards),
        },
        "columns": columns,
        "generated_at": clock.now().isoformat(),
    }


def move_card(user: dict, opp_id: int, payload: dict, args: dict) -> dict:
    """Kéo thả thẻ sang cột khác = chuyển giai đoạn (áp dụng điều kiện SCRUM-90)."""
    params = validate(args, BOARD_SCHEMA)
    result = gates.change_stage(user, opp_id, payload, allow_same=True)

    # Thẻ vừa di chuyển và số liệu mới của các cột liên quan (theo cùng bộ lọc đang xem)
    today = clock.today()
    stages = {s["id"]: s for s in list_stages()}
    record = row(CARD_SELECT + " WHERE o.id = ?", (opp_id,))
    card = _card(record, stages[record["stage_id"]], today)

    condition, values, _ = _filters(user, params)
    affected = {result["opportunity"]["stage"]["id"]}
    if result["changed"]:
        history = row("SELECT from_stage_id FROM opportunity_stage_history WHERE opportunity_id = ? "
                      "ORDER BY id DESC LIMIT 1", (opp_id,))
        if history and history["from_stage_id"]:
            affected.add(history["from_stage_id"])
    columns = []
    for stage_id in sorted(affected, key=lambda sid: stages[sid]["sort_order"]):
        records = rows(CARD_SELECT + f" WHERE {condition} AND o.stage_id = ?", [*values, stage_id])
        cards = [_card(r, stages[stage_id], today) for r in records]
        totals = _column_totals(cards)
        columns.append({"stage_id": stage_id, "stage_name": stages[stage_id]["name"], **totals})
    return {
        "message": result["message"],
        "changed": result["changed"],
        "override_applied": result["override_applied"],
        "card": card,
        "columns": columns,
    }
