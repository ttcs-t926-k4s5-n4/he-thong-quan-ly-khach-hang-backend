"""
app/opportunities.py — Quản lý Cơ hội kinh doanh tích hợp Trường tùy chỉnh (SCRUM-66)
"""
import time
from typing import Any

from app.custom_fields import (
    batch_get_custom_field_values,
    save_custom_field_values,
    validate_custom_fields,
)
from app.db import fetch_all, fetch_one, get_db


def _now_ms() -> int:
    return int(time.time() * 1000)


def list_opportunities(
    q: str = "",
    stage: str = "",
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
        where_clauses.append("o.stage = ?")
        params.append(stage.strip())

    if customer_id:
        where_clauses.append("o.customer_id = ?")
        params.append(customer_id)

    # Lọc theo trường tùy chỉnh của Cơ hội
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
        SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.expected_close_date,
               o.created_by, u.full_name AS creator_name, o.created_at, o.updated_at
        FROM dbo.opportunities o
        LEFT JOIN dbo.customers c ON o.customer_id = c.id
        LEFT JOIN dbo.users u ON o.created_by = u.id
        WHERE {where_sql}
        ORDER BY o.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    page_params = params + [offset, per_page]
    items = fetch_all(conn, sql, page_params)

    # Convert Decimal to float for JSON output
    for item in items:
        if item.get("value") is not None:
            item["value"] = float(item["value"])

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
        SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.expected_close_date,
               o.created_by, u.full_name AS creator_name, o.created_at, o.updated_at
        FROM dbo.opportunities o
        LEFT JOIN dbo.customers c ON o.customer_id = c.id
        LEFT JOIN dbo.users u ON o.created_by = u.id
        WHERE o.id = ?
        """,
        (opportunity_id,),
    )
    if not row:
        return None

    if row.get("value") is not None:
        row["value"] = float(row["value"])

    cf_map = batch_get_custom_field_values(conn, "opportunity", [opportunity_id])
    row["custom_fields"] = cf_map.get(opportunity_id, {})
    return row


def create_opportunity(
    title: str,
    customer_id: int,
    value: float = 0.0,
    stage: str = "Mới tạo",
    expected_close_date: str = "",
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

    cf_input = custom_fields or {}
    is_valid, clean_cf, cf_errors = validate_custom_fields("opportunity", cf_input)
    if not is_valid:
        raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.opportunities (title, customer_id, value, stage, expected_close_date, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, customer_id, float(value), stage.strip() or "Mới tạo", expected_close_date.strip(), created_by, now, now),
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
    expected_close_date: str = "",
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

    cf_input = custom_fields or {}
    is_valid, clean_cf, cf_errors = validate_custom_fields("opportunity", cf_input)
    if not is_valid:
        raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.opportunities
        SET title = ?, customer_id = ?, value = ?, stage = ?, expected_close_date = ?, updated_at = ?
        WHERE id = ?
        """,
        (title, customer_id, float(value), stage.strip() or "Mới tạo", expected_close_date.strip(), now, opportunity_id),
    )

    save_custom_field_values(conn, "opportunity", opportunity_id, clean_cf)
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
