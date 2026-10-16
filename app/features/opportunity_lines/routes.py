"""SCRUM-89 – API danh mục sản phẩm và dòng sản phẩm/dịch vụ của cơ hội."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.db import commit, row
from app.errors import NotFound
from app.validation import json_body, query_args
from . import service

bp = Blueprint("opportunity_lines", __name__)


@bp.get("/api/products")
@login_required
def products():
    """[SCRUM-89] Danh mục sản phẩm/dịch vụ kèm đơn giá niêm yết hiện hành."""
    return jsonify(service.list_products(query_args()))


@bp.get("/api/products/<int:product_id>")
@login_required
def product_detail(product_id: int):
    """[SCRUM-89] Chi tiết sản phẩm/dịch vụ kèm giá niêm yết."""
    product = row("SELECT * FROM products WHERE id = ?", (product_id,))
    if product is None:
        raise NotFound("Không tìm thấy sản phẩm/dịch vụ.")
    return jsonify(service.product_out(product, service.current_price_list()))


@bp.get("/api/opportunities/<int:opp_id>/lines")
@login_required
def list_lines(opp_id: int):
    """[SCRUM-89] Các dòng sản phẩm của cơ hội và tổng giá trị hợp đồng."""
    return jsonify(service.list_lines(current_user(), opp_id))


@bp.post("/api/opportunities/<int:opp_id>/lines")
@login_required
def add_line(opp_id: int):
    """[SCRUM-89] Thêm sản phẩm/dịch vụ vào cơ hội (đơn giá mặc định theo bảng giá niêm yết)."""
    result = service.add_line(current_user(), opp_id, json_body())
    commit()
    return jsonify(result), 201


@bp.patch("/api/opportunities/<int:opp_id>/lines/<int:line_id>")
@login_required
def update_line(opp_id: int, line_id: int):
    """[SCRUM-89] Sửa số lượng, đơn giá, chiết khấu, số kỳ của một dòng (unit_price = null để về giá niêm yết)."""
    result = service.update_line(current_user(), opp_id, line_id, json_body())
    commit()
    return jsonify(result)


@bp.delete("/api/opportunities/<int:opp_id>/lines/<int:line_id>")
@login_required
def delete_line(opp_id: int, line_id: int):
    """[SCRUM-89] Xoá một dòng sản phẩm, giá trị cơ hội được tính lại."""
    result = service.delete_line(current_user(), opp_id, line_id)
    commit()
    return jsonify(result)
