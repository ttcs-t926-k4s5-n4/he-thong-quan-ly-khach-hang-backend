"""SCRUM-90 – API điều kiện bắt buộc khi rời giai đoạn, chuyển giai đoạn và ghi đè."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.db import commit
from app.validation import json_body, query_args
from . import service

bp = Blueprint("stage_gates", __name__)


@bp.get("/api/stage-rules")
@login_required
def list_rules():
    """[SCRUM-90] Danh sách điều kiện khi rời giai đoạn (lọc theo stage_id, is_active)."""
    return jsonify(service.list_rules(query_args()))


@bp.post("/api/stage-rules")
@login_required
def create_rule():
    """[SCRUM-90] Thêm điều kiện bắt buộc khi rời giai đoạn (Giám đốc kinh doanh)."""
    result = service.create_rule(current_user(), json_body())
    commit()
    return jsonify(result), 201


@bp.get("/api/stage-rules/<int:rule_id>")
@login_required
def get_rule(rule_id: int):
    """[SCRUM-90] Xem một điều kiện chuyển giai đoạn."""
    return jsonify(service.rule_out(service.get_rule(rule_id)))


@bp.patch("/api/stage-rules/<int:rule_id>")
@login_required
def update_rule(rule_id: int):
    """[SCRUM-90] Sửa / bật / tắt điều kiện chuyển giai đoạn (Giám đốc kinh doanh)."""
    result = service.update_rule(current_user(), rule_id, json_body())
    commit()
    return jsonify(result)


@bp.delete("/api/stage-rules/<int:rule_id>")
@login_required
def delete_rule(rule_id: int):
    """[SCRUM-90] Xoá điều kiện chuyển giai đoạn (Giám đốc kinh doanh)."""
    result = service.delete_rule(current_user(), rule_id)
    commit()
    return jsonify(result)


@bp.get("/api/stage-rules/overrides")
@login_required
def override_log():
    """[SCRUM-90] Nhật ký các lần ghi đè điều kiện (Trưởng nhóm trở lên)."""
    return jsonify(service.override_log(current_user(), query_args()))


@bp.get("/api/opportunities/<int:opp_id>/stage-check")
@login_required
def stage_check(opp_id: int):
    """[SCRUM-90] Kiểm tra trước cơ hội đã đủ điều kiện sang giai đoạn đích (to_stage_id) chưa."""
    return jsonify(service.stage_check(current_user(), opp_id, query_args()))


@bp.post("/api/opportunities/<int:opp_id>/change-stage")
@login_required
def change_stage(opp_id: int):
    """[SCRUM-90] Chuyển giai đoạn cơ hội; bị chặn nếu thiếu điều kiện, trưởng nhóm có thể ghi đè kèm lý do."""
    result = service.change_stage(current_user(), opp_id, json_body())
    commit()
    return jsonify(result)


@bp.get("/api/opportunities/<int:opp_id>/stage-history")
@login_required
def stage_history(opp_id: int):
    """[SCRUM-90] Lịch sử chuyển giai đoạn của cơ hội, gồm các lần ghi đè và lý do."""
    return jsonify(service.stage_history(current_user(), opp_id))
