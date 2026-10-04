"""API REST. Tất cả endpoint dữ liệu đều yêu cầu đăng nhập và đi qua phân quyền."""
from datetime import datetime

from flask import Blueprint, g, jsonify, request, send_file

from . import messages
from .auth import login_required
from .db import get_db
from .export import build_workbook
from .repository import get_record, list_records
from .resources import RESOURCES
from .scope import available_scopes, max_scope, resolve_scope

bp = Blueprint("api", __name__, url_prefix="/api")


def _resource(name: str):
    resource = RESOURCES.get(name)
    if resource is None:
        raise messages.unknown_resource(name)
    return resource


def _int_arg(name: str, default: int, maximum: int = 200) -> int:
    try:
        value = int(request.args.get(name, default))
    except ValueError:
        value = default
    return max(1, min(value, maximum))


@bp.get("/me")
@login_required
def me():
    user = g.user
    return jsonify({
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "role_label": messages.ROLE_LABELS[user.role.value],
        "team_id": user.team_id,
        "max_scope": max_scope(user).value,
        "available_scopes": [{"value": s.value, "label": messages.SCOPE_LABELS[s.value]}
                             for s in available_scopes(user)],
    })


@bp.get("/<resource_name>")
@login_required
def list_view(resource_name):
    resource = _resource(resource_name)
    scope = resolve_scope(g.user, request.args.get("scope"))
    page = _int_arg("page", 1, maximum=10_000)
    page_size = _int_arg("page_size", 20)
    rows, total = list_records(get_db(), resource, g.user, scope,
                               q=request.args.get("q"), page=page, page_size=page_size)
    return jsonify({"scope": scope.value, "scope_label": messages.SCOPE_LABELS[scope.value],
                    "page": page, "page_size": page_size, "total": total, "items": rows})


@bp.get("/<resource_name>/export")
@login_required
def export_view(resource_name):
    resource = _resource(resource_name)
    scope = resolve_scope(g.user, request.args.get("scope"))
    rows, _ = list_records(get_db(), resource, g.user, scope,
                           q=request.args.get("q"), paginate=False)
    buffer = build_workbook(resource, rows, scope.value, g.user.full_name)
    filename = f"{resource.name}_{scope.value}_{datetime.now():%Y%m%d_%H%M}.xlsx"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@bp.get("/<resource_name>/<int:record_id>")
@login_required
def detail_view(resource_name, record_id):
    resource = _resource(resource_name)
    return jsonify(get_record(get_db(), resource, g.user, record_id))
