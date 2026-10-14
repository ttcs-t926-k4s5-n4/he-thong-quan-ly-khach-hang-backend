"""Danh mục tra cứu dùng chung cho giao diện (giai đoạn, khách hàng, người dùng, nhãn tiếng Việt)."""
from flask import Blueprint, jsonify

from app import labels
from app.auth import current_user, login_required
from app.common.access import get_visible_customer
from app.common.stages import list_stages, stage_out
from app.db import rows
from app.errors import NotFound
from app.permissions import owner_scope, sees_everything
from app.validation import Str, query_args, validate

bp = Blueprint("lookups", __name__, url_prefix="/api/lookups")


@bp.get("/enums")
@login_required
def enums():
    """Nhãn tiếng Việt của mọi giá trị mã hoá (loại hoạt động, mức ưu tiên, nguồn cơ hội...)."""
    return jsonify({
        "roles": labels.choices_out(labels.ROLES),
        "opportunity_sources": labels.choices_out(labels.OPPORTUNITY_SOURCES),
        "opportunity_statuses": labels.choices_out(labels.OPPORTUNITY_STATUSES),
        "product_types": labels.choices_out(labels.PRODUCT_TYPES),
        "billing_periods": labels.choices_out(labels.BILLING_PERIODS),
        "activity_types": labels.choices_out(labels.ACTIVITY_TYPES),
        "activity_statuses": labels.choices_out(labels.ACTIVITY_STATUSES),
        "task_priorities": labels.choices_out(labels.TASK_PRIORITIES),
        "task_statuses": labels.choices_out(labels.TASK_STATUSES),
        "stage_rule_types": labels.choices_out(labels.RULE_TYPES),
        "stage_rule_fields": labels.choices_out(labels.RULE_FIELDS),
    })


@bp.get("/stages")
@login_required
def stages():
    """Danh sách giai đoạn pipeline theo thứ tự."""
    return jsonify({"items": [stage_out(s) for s in list_stages()]})


@bp.get("/customers")
@login_required
def customers():
    """Khách hàng trong phạm vi quyền của bạn (tìm theo tên, không phân biệt dấu)."""
    args = validate(query_args(), {"q": Str("Từ khoá", max_len=100)})
    user = current_user()
    scope, params = owner_scope(user, "c.owner_id")
    sql = ("SELECT c.id, c.name, c.phone, c.email, c.owner_id, u.full_name AS owner_name "
           f"FROM customers c JOIN users u ON u.id = c.owner_id WHERE {scope}")
    if args["q"]:
        sql += " AND search_text(c.name) LIKE ?"
        params = [*params, f"%{labels.search_text(args['q'])}%"]
    items = rows(sql + " ORDER BY c.name LIMIT 50", params)
    return jsonify({"items": [{
        "id": r["id"], "name": r["name"], "phone": r["phone"], "email": r["email"],
        "owner": {"id": r["owner_id"], "full_name": r["owner_name"]},
    } for r in items]})


@bp.get("/customers/<int:customer_id>/contacts")
@login_required
def customer_contacts(customer_id: int):
    """Người liên hệ của một khách hàng."""
    customer = get_visible_customer(current_user(), customer_id)
    if customer is None:
        raise NotFound("Không tìm thấy khách hàng hoặc bạn không có quyền với khách hàng này.")
    items = rows("SELECT id, full_name, job_title, phone, email FROM contacts WHERE customer_id = ? "
                 "ORDER BY full_name", (customer_id,))
    return jsonify({"customer": {"id": customer["id"], "name": customer["name"]}, "items": items})


@bp.get("/users")
@login_required
def users():
    """Người dùng bạn được xem/giao việc: nhân viên thấy chính mình, trưởng nhóm thấy cả nhóm."""
    user = current_user()
    scope, params = owner_scope(user, "u.id")
    items = rows("SELECT u.id, u.full_name, u.role, u.team_id, t.name AS team_name FROM users u "
                 f"LEFT JOIN teams t ON t.id = u.team_id WHERE u.is_active = 1 AND {scope} "
                 "ORDER BY u.full_name", params)
    return jsonify({"items": [{
        "id": r["id"], "full_name": r["full_name"], "role": r["role"],
        "role_label": labels.ROLES.get(r["role"], r["role"]),
        "team": {"id": r["team_id"], "name": r["team_name"]} if r["team_id"] else None,
    } for r in items]})


@bp.get("/teams")
@login_required
def teams():
    """Các nhóm kinh doanh trong phạm vi quyền."""
    user = current_user()
    if sees_everything(user):
        items = rows("SELECT id, name FROM teams ORDER BY name")
    else:
        items = rows("SELECT id, name FROM teams WHERE id = ?", (user.get("team_id"),))
    return jsonify({"items": items})
