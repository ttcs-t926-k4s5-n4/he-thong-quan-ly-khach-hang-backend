"""SCRUM-87 – API tạo và quản lý cơ hội bán hàng."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.db import commit
from app.validation import json_body, query_args
from . import service

bp = Blueprint("opportunities", __name__, url_prefix="/api/opportunities")


@bp.post("")
@login_required
def create():
    """[SCRUM-87] Tạo cơ hội bán hàng mới."""
    result = service.create_opportunity(current_user(), json_body())
    commit()
    return jsonify(result), 201


@bp.get("")
@login_required
def list_all():
    """[SCRUM-87] Danh sách cơ hội trong phạm vi quyền (lọc khách hàng, giai đoạn, trạng thái, ngày chốt)."""
    return jsonify(service.list_opportunities(current_user(), query_args()))


@bp.get("/<int:opp_id>")
@login_required
def detail(opp_id: int):
    """[SCRUM-87] Chi tiết một cơ hội."""
    return jsonify(service.get_opportunity(current_user(), opp_id))


@bp.patch("/<int:opp_id>")
@login_required
def update(opp_id: int):
    """[SCRUM-87] Cập nhật thông tin cơ hội (xác suất sửa tay phải kèm ghi chú)."""
    result = service.update_opportunity(current_user(), opp_id, json_body())
    commit()
    return jsonify(result)


@bp.delete("/<int:opp_id>")
@login_required
def delete(opp_id: int):
    """[SCRUM-87] Xoá (ẩn) cơ hội."""
    result = service.delete_opportunity(current_user(), opp_id)
    commit()
    return jsonify(result)
