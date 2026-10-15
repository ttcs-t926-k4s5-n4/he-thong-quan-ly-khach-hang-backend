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
