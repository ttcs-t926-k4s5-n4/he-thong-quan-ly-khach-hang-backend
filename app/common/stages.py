"""Truy vấn giai đoạn pipeline (dùng chung)."""
from __future__ import annotations

from app.db import row, rows


def list_stages(include_inactive: bool = False) -> list[dict]:
    where = "" if include_inactive else " WHERE is_active = 1"
    return rows(f"SELECT * FROM pipeline_stages{where} ORDER BY sort_order, id")


def get_stage(stage_id) -> dict | None:
    return row("SELECT * FROM pipeline_stages WHERE id = ?", (stage_id,))


def first_open_stage() -> dict | None:
    return row("SELECT * FROM pipeline_stages WHERE is_active = 1 AND is_won = 0 AND is_lost = 0 "
               "ORDER BY sort_order, id LIMIT 1")


def is_closed(stage: dict) -> bool:
    return bool(stage["is_won"] or stage["is_lost"])


def stage_out(stage: dict) -> dict:
    return {
        "id": stage["id"],
        "code": stage["code"],
        "name": stage["name"],
        "sort_order": stage["sort_order"],
        "default_probability": stage["default_probability"],
        "stale_after_days": stage["stale_after_days"],
        "is_won": bool(stage["is_won"]),
        "is_lost": bool(stage["is_lost"]),
        "is_closed": is_closed(stage),
    }
