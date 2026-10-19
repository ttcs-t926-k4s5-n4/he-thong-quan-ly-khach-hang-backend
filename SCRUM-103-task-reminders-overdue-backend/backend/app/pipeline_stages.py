"""
app/pipeline_stages.py — Cấu hình giai đoạn Pipeline, xác suất thắng & dự báo doanh số (S2-09)
Dành cho Giám đốc kinh doanh (Sales Manager)
"""
import json
import re
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db


def _now_ms() -> int:
    return int(time.time() * 1000)


def sanitize_stage_key(key: str) -> str:
    key = key.strip().lower()
    key = re.sub(r"[^a-z0-9_]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def list_pipeline_stages(is_active_only: bool = False) -> list[dict[str, Any]]:
    conn = get_db()
    sql = """
        SELECT id, stage_key, stage_name, win_probability, display_order,
               required_conditions_json, is_won_stage, is_lost_stage, is_active,
               created_at, updated_at
        FROM dbo.pipeline_stages
        WHERE 1=1
    """
    params: list[Any] = []
    if is_active_only:
        sql += " AND is_active = 1"

    sql += " ORDER BY display_order ASC, id ASC"
    rows = fetch_all(conn, sql, params)

    for r in rows:
        r["is_won_stage"] = bool(r["is_won_stage"])
        r["is_lost_stage"] = bool(r["is_lost_stage"])
        r["is_active"] = bool(r["is_active"])
        if r["required_conditions_json"]:
            try:
                r["required_conditions"] = json.loads(r["required_conditions_json"])
            except Exception:
                r["required_conditions"] = {}
        else:
            r["required_conditions"] = {}

    return rows


def get_pipeline_stage(stage_id: int) -> dict[str, Any] | None:
    conn = get_db()
    r = fetch_one(
        conn,
        """
        SELECT id, stage_key, stage_name, win_probability, display_order,
               required_conditions_json, is_won_stage, is_lost_stage, is_active,
               created_at, updated_at
        FROM dbo.pipeline_stages
        WHERE id = ?
        """,
        (stage_id,),
    )
    if not r:
        return None

    r["is_won_stage"] = bool(r["is_won_stage"])
    r["is_lost_stage"] = bool(r["is_lost_stage"])
    r["is_active"] = bool(r["is_active"])
    if r["required_conditions_json"]:
        try:
            r["required_conditions"] = json.loads(r["required_conditions_json"])
        except Exception:
            r["required_conditions"] = {}
    else:
        r["required_conditions"] = {}
    return r


def get_pipeline_stage_by_key(stage_key: str) -> dict[str, Any] | None:
    conn = get_db()
    r = fetch_one(
        conn,
        """
        SELECT id, stage_key, stage_name, win_probability, display_order,
               required_conditions_json, is_won_stage, is_lost_stage, is_active,
               created_at, updated_at
        FROM dbo.pipeline_stages
        WHERE stage_key = ?
        """,
        (stage_key.strip().lower(),),
    )
    if not r:
        return None
    r["is_won_stage"] = bool(r["is_won_stage"])
    r["is_lost_stage"] = bool(r["is_lost_stage"])
    r["is_active"] = bool(r["is_active"])
    if r["required_conditions_json"]:
        try:
            r["required_conditions"] = json.loads(r["required_conditions_json"])
        except Exception:
            r["required_conditions"] = {}
    else:
        r["required_conditions"] = {}
    return r


def create_pipeline_stage(
    stage_key: str,
    stage_name: str,
    win_probability: int = 0,
    display_order: int = 0,
    required_conditions: dict[str, Any] | str | None = None,
    is_won_stage: bool = False,
    is_lost_stage: bool = False,
    is_active: bool = True,
) -> dict[str, Any]:
    clean_key = sanitize_stage_key(stage_key)
    if not clean_key:
        raise ValueError("stage_key_invalid")

    stage_name = stage_name.strip()
    if not stage_name:
        raise ValueError("stage_name_empty")

    win_prob = max(0, min(100, int(win_probability)))

    req_json = None
    if isinstance(required_conditions, dict):
        req_json = json.dumps(required_conditions, ensure_ascii=False)
    elif isinstance(required_conditions, str) and required_conditions.strip():
        req_json = required_conditions.strip()

    conn = get_db()
    existing = fetch_one(conn, "SELECT id FROM dbo.pipeline_stages WHERE stage_key = ?", (clean_key,))
    if existing:
        raise ValueError("duplicate_stage_key")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.pipeline_stages
        (stage_key, stage_name, win_probability, display_order, required_conditions_json, is_won_stage, is_lost_stage, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            clean_key,
            stage_name,
            win_prob,
            int(display_order),
            req_json,
            1 if is_won_stage else 0,
            1 if is_lost_stage else 0,
            1 if is_active else 0,
            now,
            now,
        ),
    )
    conn.commit()

    new_stage = fetch_one(conn, "SELECT id FROM dbo.pipeline_stages WHERE stage_key = ?", (clean_key,))
    return get_pipeline_stage(new_stage["id"])  # type: ignore


def update_pipeline_stage(
    stage_id: int,
    stage_name: str,
    win_probability: int = 0,
    display_order: int = 0,
    required_conditions: dict[str, Any] | str | None = None,
    is_won_stage: bool = False,
    is_lost_stage: bool = False,
    is_active: bool = True,
) -> dict[str, Any]:
    existing = get_pipeline_stage(stage_id)
    if not existing:
        raise LookupError("stage_not_found")

    stage_name = stage_name.strip()
    if not stage_name:
        raise ValueError("stage_name_empty")

    win_prob = max(0, min(100, int(win_probability)))

    req_json = None
    if isinstance(required_conditions, dict):
        req_json = json.dumps(required_conditions, ensure_ascii=False)
    elif isinstance(required_conditions, str) and required_conditions.strip():
        req_json = required_conditions.strip()

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.pipeline_stages
        SET stage_name = ?, win_probability = ?, display_order = ?, required_conditions_json = ?,
            is_won_stage = ?, is_lost_stage = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            stage_name,
            win_prob,
            int(display_order),
            req_json,
            1 if is_won_stage else 0,
            1 if is_lost_stage else 0,
            1 if is_active else 0,
            now,
            stage_id,
        ),
    )
    conn.commit()
    return get_pipeline_stage(stage_id)  # type: ignore


def delete_pipeline_stage(stage_id: int) -> bool:
    conn = get_db()
    existing = get_pipeline_stage(stage_id)
    if not existing:
        raise LookupError("stage_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.pipeline_stages WHERE id = ?", (stage_id,))
    conn.commit()
    return True


def validate_stage_transition(conn, opportunity_id: int, target_stage_key: str, meetings_count: int = 0) -> tuple[bool, str | None]:
    """
    Kiểm tra điều kiện chuyển giai đoạn (Exit Conditions):
    VD: Nếu giai đoạn yêu cầu ít nhất 1 cuộc gặp (min_meetings >= 1) mà chưa có -> Từ chối chuyển giai đoạn.
    """
    target_stage = get_pipeline_stage_by_key(target_stage_key)
    if not target_stage:
        return True, None

    reqs = target_stage.get("required_conditions", {})
    if not reqs:
        return True, None

    # Kiểm tra số cuộc gặp tối thiểu
    min_meetings = reqs.get("min_meetings", 0)
    if min_meetings > 0 and meetings_count < min_meetings:
        return False, f"Giai đoạn '{target_stage['stage_name']}' yêu cầu phải có ít nhất {min_meetings} cuộc gặp (Hiện tại: {meetings_count})."

    return True, None


def get_sales_forecast_summary() -> dict[str, Any]:
    """
    Tính toán báo cáo Dự báo doanh số (Sales Forecast Engine):
    Doanh số dự báo = Giá trị cơ hội * (Xác suất thắng / 100)
    """
    conn = get_db()
    stages = list_pipeline_stages(is_active_only=True)
    stages_by_key = {s["stage_key"]: s for s in stages}

    sql = """
        SELECT o.id, o.title, o.value, o.stage, o.stage_key, o.win_probability
        FROM dbo.opportunities o
    """
    rows = fetch_all(conn, sql)

    forecast_by_stage: dict[str, dict[str, Any]] = {}
    total_pipeline_value = 0.0
    total_forecast_amount = 0.0

    for s in stages:
        skey = s["stage_key"]
        forecast_by_stage[skey] = {
            "stage_key": skey,
            "stage_name": s["stage_name"],
            "default_win_probability": s["win_probability"],
            "count": 0,
            "total_value": 0.0,
            "forecast_amount": 0.0,
        }

    for r in rows:
        val = float(r["value"] or 0.0)
        skey = r.get("stage_key") or "initial"
        prob = r.get("win_probability")

        if skey not in forecast_by_stage:
            # Fallback nếu stage chưa nằm trong list active
            stage_def = stages_by_key.get(skey)
            prob = prob if prob is not None else (stage_def["win_probability"] if stage_def else 0)
            forecast_by_stage[skey] = {
                "stage_key": skey,
                "stage_name": r.get("stage") or skey,
                "default_win_probability": prob,
                "count": 0,
                "total_value": 0.0,
                "forecast_amount": 0.0,
            }
        else:
            if prob is None:
                prob = forecast_by_stage[skey]["default_win_probability"]

        forecast_val = val * (prob / 100.0)

        forecast_by_stage[skey]["count"] += 1
        forecast_by_stage[skey]["total_value"] += val
        forecast_by_stage[skey]["forecast_amount"] += forecast_val

        total_pipeline_value += val
        total_forecast_amount += forecast_val

    return {
        "summary_by_stage": list(forecast_by_stage.values()),
        "total_pipeline_value": total_pipeline_value,
        "total_forecast_amount": total_forecast_amount,
    }
