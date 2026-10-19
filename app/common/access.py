"""Truy xuất dữ liệu dùng chung kèm kiểm tra phạm vi quyền."""
from __future__ import annotations

from app import clock
from app.db import row
from app.errors import NotFound, ValidationFailed
from app.labels import AMOUNT_SOURCES, OPPORTUNITY_SOURCES, OPPORTUNITY_STATUSES, round_vnd
from app.permissions import owner_scope
from app.validation import field_error, invalid

# ---------------------------------------------------------------- Người dùng / khách hàng

def get_active_user(user_id) -> dict | None:
    return row("SELECT u.id, u.username, u.full_name, u.role, u.team_id, u.is_active, t.name AS team_name "
               "FROM users u LEFT JOIN teams t ON t.id = u.team_id WHERE u.id = ? AND u.is_active = 1",
               (user_id,))


def get_any_user(user_id) -> dict | None:
    return row("SELECT u.id, u.username, u.full_name, u.role, u.team_id, u.is_active FROM users u WHERE u.id = ?",
               (user_id,))


def get_visible_customer(user: dict, customer_id) -> dict | None:
    scope, params = owner_scope(user, "c.owner_id")
    return row(f"SELECT c.* FROM customers c WHERE c.id = ? AND {scope}", (customer_id, *params))


def get_contact(contact_id) -> dict | None:
    return row("SELECT * FROM contacts WHERE id = ?", (contact_id,))


# ---------------------------------------------------------------- Cơ hội

OPP_SELECT = """
SELECT o.*,
       c.name AS customer_name, c.owner_id AS customer_owner_id,
       ct.full_name AS contact_name, ct.job_title AS contact_job_title,
       s.name AS stage_name, s.code AS stage_code, s.sort_order AS stage_sort_order,
       s.default_probability AS stage_default_probability, s.stale_after_days AS stage_stale_after_days,
       s.is_won AS stage_is_won, s.is_lost AS stage_is_lost,
       u.full_name AS owner_name, u.team_id AS owner_team_id
FROM opportunities o
JOIN customers c ON c.id = o.customer_id
LEFT JOIN contacts ct ON ct.id = o.primary_contact_id
JOIN pipeline_stages s ON s.id = o.stage_id
JOIN users u ON u.id = o.owner_id
"""


def find_visible_opportunity(user: dict, opp_id) -> dict | None:
    scope, params = owner_scope(user, "o.owner_id")
    return row(OPP_SELECT + f" WHERE o.id = ? AND o.is_deleted = 0 AND {scope}", (opp_id, *params))


def get_visible_opportunity(user: dict, opp_id) -> dict:
    opp = find_visible_opportunity(user, opp_id)
    if opp is None:
        raise NotFound("Không tìm thấy cơ hội hoặc bạn không có quyền truy cập cơ hội này.")
    return opp


def opportunity_status(opp: dict) -> str:
    if opp["stage_is_won"]:
        return "won"
    if opp["stage_is_lost"]:
        return "lost"
    return "open"


def serialize_opportunity(opp: dict) -> dict:
    status = opportunity_status(opp)
    return {
        "id": opp["id"],
        "name": opp["name"],
        "customer": {"id": opp["customer_id"], "name": opp["customer_name"]},
        "primary_contact": ({"id": opp["primary_contact_id"], "full_name": opp["contact_name"],
                             "job_title": opp["contact_job_title"]} if opp["primary_contact_id"] else None),
        "stage": {"id": opp["stage_id"], "code": opp["stage_code"], "name": opp["stage_name"],
                  "is_closed": status != "open"},
        "status": status,
        "status_label": OPPORTUNITY_STATUSES[status],
        "estimated_value": opp["estimated_value"],
        "amount": opp["amount"],
        "amount_source": opp["amount_source"],
        "amount_source_label": AMOUNT_SOURCES[opp["amount_source"]],
        "recurring_annual_value": opp["recurring_annual_value"],
        "weighted_amount": round_vnd(opp["amount"] * opp["probability"] / 100),
        "expected_close_date": opp["expected_close_date"],
        "source": opp["source"],
        "source_label": OPPORTUNITY_SOURCES.get(opp["source"], opp["source"]),
        "description": opp["description"],
        "probability": opp["probability"],
        "probability_default": opp["stage_default_probability"],
        "probability_is_manual": bool(opp["probability_is_manual"]),
        "probability_note": opp["probability_note"],
        "owner": {"id": opp["owner_id"], "full_name": opp["owner_name"]},
        "stage_entered_at": clock.iso(opp["stage_entered_at"]),
        "closed_at": clock.iso(opp["closed_at"]),
        "created_at": clock.iso(opp["created_at"]),
        "updated_at": clock.iso(opp["updated_at"]),
    }


# ---------------------------------------------------------------- Liên kết khách hàng / người liên hệ / cơ hội

def resolve_customer_links(user: dict, customer_id, contact_id, opportunity_id):
    """Xác định khách hàng, người liên hệ, cơ hội cho hoạt động/công việc và kiểm tra tính nhất quán.

    - Chỉ gửi cơ hội hoặc người liên hệ thì khách hàng được suy ra tự động.
    - Người liên hệ và cơ hội phải thuộc đúng khách hàng.
    - Người dùng phải có quyền với khách hàng (hoặc với cơ hội được chọn).
    """
    errors = []
    opp = None
    if opportunity_id is not None:
        opp = find_visible_opportunity(user, opportunity_id)
        if opp is None:
            errors.append(field_error("opportunity_id", "Cơ hội",
                                      "Cơ hội không tồn tại hoặc bạn không có quyền với cơ hội này."))
    contact = None
    if contact_id is not None:
        contact = get_contact(contact_id)
        if contact is None:
            errors.append(field_error("contact_id", "Người liên hệ", "Người liên hệ không tồn tại."))
    if errors:
        raise ValidationFailed(errors)

    if customer_id is None:
        customer_id = opp["customer_id"] if opp else (contact["customer_id"] if contact else None)
    if customer_id is None:
        raise invalid("customer_id", "Khách hàng", "Vui lòng chọn khách hàng hoặc cơ hội liên quan.")

    customer = row("SELECT * FROM customers WHERE id = ?", (customer_id,))
    if customer is None or (opp is None and get_visible_customer(user, customer_id) is None):
        raise invalid("customer_id", "Khách hàng",
                      "Khách hàng không tồn tại hoặc bạn không có quyền với khách hàng này.")
    if opp is not None and opp["customer_id"] != customer["id"]:
        errors.append(field_error("opportunity_id", "Cơ hội", "Cơ hội đã chọn không thuộc khách hàng này."))
    if contact is not None and contact["customer_id"] != customer["id"]:
        errors.append(field_error("contact_id", "Người liên hệ",
                                  "Người liên hệ đã chọn không thuộc khách hàng này."))
    if errors:
        raise ValidationFailed(errors)
    return customer, contact, opp
