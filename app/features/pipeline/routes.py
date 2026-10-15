"""SCRUM-88 – API bảng pipeline dạng kanban."""
from flask import Blueprint, jsonify

from app.auth import current_user, login_required
from app.common.stages import list_stages, stage_out
from app.db import commit
from app.validation import json_body, query_args
from . import service

bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")


@bp.get("/board")
@login_required
def board():
    """[SCRUM-88] Bảng kanban: cột theo giai đoạn, số cơ hội, tổng giá trị, thẻ kèm cảnh báo đình trệ."""
    return jsonify(service.get_board(current_user(), query_args()))


@bp.post("/cards/<int:opp_id>/move")
@login_required
def move(opp_id: int):
    """[SCRUM-88] Kéo thả thẻ cơ hội sang cột (giai đoạn) khác; trả về thẻ và số liệu cột mới."""
    result = service.move_card(current_user(), opp_id, json_body(), query_args())
    commit()
    return jsonify(result)


@bp.get("/stages")
@login_required
def stages():
    """[SCRUM-88] Các cột (giai đoạn) của bảng pipeline."""
    return jsonify({"items": [stage_out(s) for s in list_stages()]})
