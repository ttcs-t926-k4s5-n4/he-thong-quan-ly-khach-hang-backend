"""SCRUM-100 – API công việc có hạn hoàn thành."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.db import commit
from app.validation import json_body, query_args
from . import service

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.post("")
@login_required
def create():
    """[SCRUM-100] Tạo công việc (tiêu đề, hạn, mức ưu tiên, người thực hiện, khách hàng/cơ hội)."""
    result = service.create_task(current_user(), json_body())
    commit()
    return jsonify(result), 201


@bp.get("")
@login_required
def list_all():
    """[SCRUM-100] Danh sách công việc (lọc trạng thái, người thực hiện, quá hạn, hôm nay, 7 ngày tới...)."""
    return jsonify(service.list_tasks(current_user(), query_args()))


@bp.get("/reminders")
@login_required
def reminders():
    """[SCRUM-100] Nhắc việc: công việc của tôi quá hạn, đến hạn hôm nay và ngày mai."""
    return jsonify(service.reminders(current_user()))


@bp.get("/<int:task_id>")
@login_required
def detail(task_id: int):
    """[SCRUM-100] Chi tiết công việc kèm lịch sử hoãn."""
    return jsonify(service.get_task(current_user(), task_id))


@bp.patch("/<int:task_id>")
@login_required
def update(task_id: int):
    """[SCRUM-100] Sửa tiêu đề, mô tả, mức ưu tiên, liên kết (lùi hạn phải dùng Hoãn)."""
    result = service.update_task(current_user(), task_id, json_body())
    commit()
    return jsonify(result)


@bp.post("/<int:task_id>/complete")
@login_required
def complete(task_id: int):
    """[SCRUM-100] Đánh dấu hoàn thành công việc."""
    result = service.complete_task(current_user(), task_id, json_body())
    commit()
    return jsonify(result)


@bp.post("/<int:task_id>/reopen")
@login_required
def reopen(task_id: int):
    """[SCRUM-100] Mở lại công việc đã hoàn thành."""
    result = service.reopen_task(current_user(), task_id)
    commit()
    return jsonify(result)


@bp.post("/<int:task_id>/postpone")
@login_required
def postpone(task_id: int):
    """[SCRUM-100] Hoãn công việc sang hạn mới, bắt buộc kèm lý do."""
    result = service.postpone_task(current_user(), task_id, json_body())
    commit()
    return jsonify(result)


@bp.post("/<int:task_id>/assign")
@login_required
def assign(task_id: int):
    """[SCRUM-100] Trưởng nhóm giao (lại) công việc cho thành viên trong nhóm."""
    result = service.assign_task(current_user(), task_id, json_body())
    commit()
    return jsonify(result)


@bp.delete("/<int:task_id>")
@login_required
def delete(task_id: int):
    """[SCRUM-100] Xoá công việc (người tạo hoặc Trưởng nhóm trở lên)."""
    result = service.delete_task(current_user(), task_id)
    commit()
    return jsonify(result)
