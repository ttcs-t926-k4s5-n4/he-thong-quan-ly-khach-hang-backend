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


