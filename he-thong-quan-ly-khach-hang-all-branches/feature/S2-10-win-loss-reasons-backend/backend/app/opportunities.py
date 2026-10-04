"""
app/opportunities.py — Quản lý Cơ hội kinh doanh tích hợp Trường tùy chỉnh (SCRUM-66), Giai đoạn Pipeline & Dự báo (S2-09), Lý do Thắng/Thua & Đối thủ (S2-10)
"""
import time
from typing import Any

from app.custom_fields import (
    batch_get_custom_field_values,
    save_custom_field_values,
    validate_custom_fields,
)
from app.db import fetch_all, fetch_one, get_db
from app.pipeline_stages import get_pipeline_stage_by_key, validate_stage_transition
from app.win_loss_reasons import validate_opportunity_closure


def _now_ms() -> int:
    return int(time.time() * 1000)


def list_opportunities(
    q: str = "",
    stage: str = "",
    stage_key: str = "",
    customer_id: int | None = None,
    cf_filters: dict[str, str] | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    conn = get_db()
    where_clauses = ["1=1"]
    params: list[Any] = []

    if q:
        where_clauses.append("(o.title LIKE ? OR c.name LIKE ?)")
        kw = f"%{q.strip()}%"
        params.extend([kw, kw])

    if stage:
        where_clauses.append("(o.stage = ? OR o.stage_key = ?)")
        params.extend([stage.strip(), stage.strip()])

    if stage_key:
        where_clauses.append("o.stage_key = ?")
        params.append(stage_key.strip().lower())

    if customer_id:
        where_clauses.append("o.customer_id = ?")
        params.append(customer_id)

    # Lọc theo trường tùy chỉnh
    if cf_filters:
        for key, val in cf_filters.items():
            if val is not None and str(val).strip() != "":
                where_clauses.append(
                    """
                    EXISTS (
                        SELECT 1 FROM dbo.custom_field_values cfv_f
                        INNER JOIN dbo.custom_field_definitions cfd_f ON cfv_f.field_id = cfd_f.id
                        WHERE cfv_f.entity_type = 'opportunity'
                          AND cfv_f.entity_id = o.id
                          AND cfd_f.field_key = ?
                          AND cfv_f.field_value LIKE ?
                    )
                    """
                )
                params.extend([key, f"%{str(val).strip()}%"])

    where_sql = " AND ".join(where_clauses)

    count_row = fetch_one(
        conn,
        f"""
        SELECT COUNT(*) AS total
        FROM dbo.opportunities o
        LEFT JOIN dbo.customers c ON o.customer_id = c.id
        WHERE {where_sql}
        """,
        params,
    )
    total = count_row["total"] if count_row else 0

    offset = (page - 1) * per_page
    sql = f"""
        SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.stage_key,
               o.win_probability, o.expected_close_date, o.meetings_count,
               o.win_reason_id, wr.reason_title AS win_reason_title,
               o.loss_reason_id, lr.reason_title AS loss_reason_title,
               o.competitor_id, comp.name AS competitor_name,
               o.closed_at, o.created_by, u.full_name AS creator_name, o.created_at, o.updated_at
        FROM dbo.opportunities o
        LEFT JOIN dbo.customers c ON o.customer_id = c.id
        LEFT JOIN dbo.users u ON o.created_by = u.id
        LEFT JOIN dbo.win_loss_reasons wr ON o.win_reason_id = wr.id
        LEFT JOIN dbo.win_loss_reasons lr ON o.loss_reason_id = lr.id
        LEFT JOIN dbo.competitors comp ON o.competitor_id = comp.id
        WHERE {where_sql}
        ORDER BY o.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    page_params = params + [offset, per_page]
    items = fetch_all(conn, sql, page_params)

    for item in items:
        val = float(item.get("value") or 0.0)
        item["value"] = val
        prob = item.get("win_probability") or 0
        item["win_probability"] = prob
        item["forecast_amount"] = val * (prob / 100.0)

    entity_ids = [item["id"] for item in items]
    cf_map = batch_get_custom_field_values(conn, "opportunity", entity_ids)

    for item in items:
        item["custom_fields"] = cf_map.get(item["id"], {})

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def get_opportunity(opportunity_id: int) -> dict[str, Any] | None:
    conn = get_db()
    row = fetch_one(
        conn,
        """
        SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.stage_key,
               o.win_probability, o.expected_close_date, o.meetings_count,
               o.win_reason_id, wr.reason_title AS win_reason_title,
               o.loss_reason_id, lr.reason_title AS loss_reason_title,
               o.competitor_id, comp.name AS competitor_name,
               o.closed_at, o.created_by, u.full_name AS creator_name, o.created_at, o.updated_at
        FROM dbo.opportunities o
        LEFT JOIN dbo.customers c ON o.customer_id = c.id
        LEFT JOIN dbo.users u ON o.created_by = u.id
        LEFT JOIN dbo.win_loss_reasons wr ON o.win_reason_id = wr.id
        LEFT JOIN dbo.win_loss_reasons lr ON o.loss_reason_id = lr.id
        LEFT JOIN dbo.competitors comp ON o.competitor_id = comp.id
        WHERE o.id = ?
        """,
        (opportunity_id,),
    )
    if not row:
        return None

    val = float(row.get("value") or 0.0)
    row["value"] = val
    prob = row.get("win_probability") or 0
    row["win_probability"] = prob
    row["forecast_amount"] = val * (prob / 100.0)

    cf_map = batch_get_custom_field_values(conn, "opportunity", [opportunity_id])
    row["custom_fields"] = cf_map.get(opportunity_id, {})
    return row


def create_opportunity(
    title: str,
    customer_id: int,
    value: float = 0.0,
    stage: str = "Mới tạo",
    stage_key: str = "",
    expected_close_date: str = "",
    meetings_count: int = 0,
    win_reason_id: int | None = None,
    loss_reason_id: int | None = None,
    competitor_id: int | None = None,
    created_by: int = 1,
    custom_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise ValueError("opportunity_title_empty")

    conn = get_db()
    customer = fetch_one(conn, "SELECT id FROM dbo.customers WHERE id = ?", (customer_id,))
    if not customer:
        raise ValueError("customer_not_found")

    # Xác định stage_key & win_probability từ pipeline stages
    s_key = stage_key.strip().lower() if stage_key else stage.strip().lower()
    stage_def = get_pipeline_stage_by_key(s_key) or get_pipeline_stage_by_key(stage.strip().lower())
    if stage_def:
        s_key = stage_def["stage_key"]
        win_prob = stage_def["win_probability"]
        stage_name = stage_def["stage_name"]
        is_won = bool(stage_def["is_won_stage"])
        is_lost = bool(stage_def["is_lost_stage"])
    else:
        s_key = s_key or "initial"
        win_prob = 10
        stage_name = stage.strip() or "Mới tạo"
        is_won = "won" in s_key or "thành công" in stage_name.lower()
        is_lost = "lost" in s_key or "thất bại" in stage_name.lower()

    # Validations đóng cơ hội (S2-10)
    is_valid_closure, closure_err = validate_opportunity_closure(
        conn, is_won=is_won, is_lost=is_lost, win_reason_id=win_reason_id, loss_reason_id=loss_reason_id, competitor_id=competitor_id
    )
    if not is_valid_closure:
        raise ValueError({"message": closure_err})

    cf_input = custom_fields or {}
    is_valid_cf, clean_cf, cf_errors = validate_custom_fields("opportunity", cf_input)
    if not is_valid_cf:
        raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})

    now = _now_ms()
    closed_at = now if (is_won or is_lost) else None

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.opportunities
        (title, customer_id, value, stage, stage_key, win_probability, expected_close_date, meetings_count,
         win_reason_id, loss_reason_id, competitor_id, closed_at, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            customer_id,
            float(value),
            stage_name,
            s_key,
            win_prob,
            expected_close_date.strip(),
            max(0, int(meetings_count)),
            win_reason_id,
            loss_reason_id,
            competitor_id,
            closed_at,
            created_by,
            now,
            now,
        ),
    )
    conn.commit()

    new_row = fetch_one(conn, "SELECT MAX(id) AS id FROM dbo.opportunities WHERE title = ? AND created_by = ?", (title, created_by))
    oid = new_row["id"]

    save_custom_field_values(conn, "opportunity", oid, clean_cf)
    conn.commit()

    return get_opportunity(oid)  # type: ignore


def update_opportunity(
    opportunity_id: int,
    title: str,
    customer_id: int,
    value: float = 0.0,
    stage: str = "Mới tạo",
    stage_key: str = "",
    expected_close_date: str = "",
    meetings_count: int = 0,
    win_reason_id: int | None = None,
    loss_reason_id: int | None = None,
    competitor_id: int | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = get_opportunity(opportunity_id)
    if not existing:
        raise LookupError("opportunity_not_found")

    title = title.strip()
    if not title:
        raise ValueError("opportunity_title_empty")

    conn = get_db()
    customer = fetch_one(conn, "SELECT id FROM dbo.customers WHERE id = ?", (customer_id,))
    if not customer:
        raise ValueError("customer_not_found")

    s_key = stage_key.strip().lower() if stage_key else stage.strip().lower()
    stage_def = get_pipeline_stage_by_key(s_key) or get_pipeline_stage_by_key(stage.strip().lower())
    if stage_def:
        s_key = stage_def["stage_key"]
        win_prob = stage_def["win_probability"]
        stage_name = stage_def["stage_name"]
        is_won = bool(stage_def["is_won_stage"])
        is_lost = bool(stage_def["is_lost_stage"])
    else:
        s_key = s_key or existing.get("stage_key") or "initial"
        win_prob = existing.get("win_probability", 10)
        stage_name = stage.strip() or existing.get("stage", "Mới tạo")
        is_won = "won" in s_key or "thành công" in stage_name.lower()
        is_lost = "lost" in s_key or "thất bại" in stage_name.lower()

    # Kiểm tra Exit Conditions khi rời/chuyển sang giai đoạn mới (S2-09)
    if s_key != existing.get("stage_key"):
        ok_trans, trans_err = validate_stage_transition(conn, opportunity_id, s_key, meetings_count=max(meetings_count, existing.get("meetings_count", 0)))
        if not ok_trans:
            raise ValueError({"message": trans_err})

    # Validations đóng cơ hội (S2-10)
    is_valid_closure, closure_err = validate_opportunity_closure(
        conn, is_won=is_won, is_lost=is_lost, win_reason_id=win_reason_id, loss_reason_id=loss_reason_id, competitor_id=competitor_id
    )
    if not is_valid_closure:
        raise ValueError({"message": closure_err})

    if custom_fields is not None:
        is_valid_cf, clean_cf, cf_errors = validate_custom_fields("opportunity", custom_fields)
        if not is_valid_cf:
            raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})
        save_custom_field_values(conn, "opportunity", opportunity_id, clean_cf)

    now = _now_ms()

    closed_at = now if (is_won or is_lost) else (existing.get("closed_at") if not (is_won or is_lost) else None)

    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.opportunities
        SET title = ?, customer_id = ?, value = ?, stage = ?, stage_key = ?, win_probability = ?,
            expected_close_date = ?, meetings_count = ?, win_reason_id = ?, loss_reason_id = ?,
            competitor_id = ?, closed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            title,
            customer_id,
            float(value),
            stage_name,
            s_key,
            win_prob,
            expected_close_date.strip(),
            max(0, int(meetings_count)),
            win_reason_id,
            loss_reason_id,
            competitor_id,
            closed_at,
            now,
            opportunity_id,
        ),
    )
    conn.commit()

    return get_opportunity(opportunity_id)  # type: ignore



def delete_opportunity(opportunity_id: int) -> bool:
    conn = get_db()
    existing = get_opportunity(opportunity_id)
    if not existing:
        raise LookupError("opportunity_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.custom_field_values WHERE entity_type = 'opportunity' AND entity_id = ?", (opportunity_id,))
    cur.execute("DELETE FROM dbo.opportunities WHERE id = ?", (opportunity_id,))
    conn.commit()
    return True
