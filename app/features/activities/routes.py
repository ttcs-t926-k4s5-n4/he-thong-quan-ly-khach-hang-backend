"""SCRUM-99 – API ghi nhận hoạt động với khách hàng."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.db import commit
from app.validation import json_body, query_args
from . import service

bp = Blueprint("activities", __name__)


@bp.post("/api/activities")
@login_required
def create():
    """[SCRUM-99] Ghi nhận hoạt động: cuộc gọi, cuộc gặp, email, ghi chú (được ghi bù hoạt động trong quá khứ)."""
    result = service.create_activity(current_user(), json_body())
    commit()
    return jsonify(result), 201


@bp.post("/api/activities/quick")
@login_required
def quick():
    """[SCRUM-99] Ghi nhanh trên điện thoại ngay sau khi rời văn phòng khách (kèm công việc tiếp theo nếu cần)."""
    result = service.quick_log(current_user(), json_body())
    commit()
    return jsonify(result), 201


@bp.get("/api/activities/quick-suggestions")
@login_required
def quick_suggestions():
    """[SCRUM-99] Gợi ý cho màn hình ghi nhanh: lịch hẹn cần cập nhật kết quả, cơ hội đang mở, khách gần đây."""
    return jsonify(service.quick_suggestions(current_user()))


@bp.get("/api/activities")
@login_required
def list_all():
    """[SCRUM-99] Danh sách hoạt động (lọc khách hàng, cơ hội, người liên hệ, loại, thời gian...)."""
    return jsonify(service.list_activities(current_user(), query_args()))


@bp.get("/api/activities/<int:activity_id>")
@login_required
def detail(activity_id: int):
    """[SCRUM-99] Chi tiết một hoạt động."""
    return jsonify(service.activity_out(service.get_visible_activity(current_user(), activity_id)))


@bp.patch("/api/activities/<int:activity_id>")
@login_required
def update(activity_id: int):
    """[SCRUM-99] Sửa hoạt động (người ghi nhận hoặc Trưởng nhóm trở lên)."""
    result = service.update_activity(current_user(), activity_id, json_body())
    commit()
    return jsonify(result)


@bp.post("/api/activities/<int:activity_id>/complete")
@login_required
def complete(activity_id: int):
    """[SCRUM-99] Cập nhật kết quả cho cuộc gọi/cuộc gặp đã lên lịch."""
    result = service.complete_activity(current_user(), activity_id, json_body())
    commit()
    return jsonify(result)


@bp.delete("/api/activities/<int:activity_id>")
@login_required
def delete(activity_id: int):
    """[SCRUM-99] Xoá hoạt động (người ghi nhận hoặc Trưởng nhóm trở lên)."""
    result = service.delete_activity(current_user(), activity_id)
    commit()
    return jsonify(result)


@bp.get("/api/customers/<int:customer_id>/activities")
@login_required
def customer_timeline(customer_id: int):
    """[SCRUM-99] Lịch sử trao đổi chung với một khách hàng (gồm hoạt động do đồng nghiệp ghi nhận)."""
    return jsonify(service.customer_timeline(current_user(), customer_id, query_args()))
