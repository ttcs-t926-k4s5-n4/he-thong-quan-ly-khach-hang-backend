"""
app/customers.py — Quản lý danh mục Khách hàng tích hợp Trường tùy chỉnh (SCRUM-66)
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


def list_customers(
    q: str = "",
    status: str = "",
    cf_filters: dict[str, str] | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    conn = get_db()
    where_clauses = ["1=1"]
    params: list[Any] = []

    if q:
        where_clauses.append("(c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ? OR c.address LIKE ?)")
        kw = f"%{q.strip()}%"
        params.extend([kw, kw, kw, kw])

    if status:
        where_clauses.append("c.status = ?")
        params.append(status.strip())

    # Lọc theo trường tùy chỉnh nếu có
    if cf_filters:
        for key, val in cf_filters.items():
            if val is not None and str(val).strip() != "":
                where_clauses.append(
                    """
                    EXISTS (
                        SELECT 1 FROM dbo.custom_field_values cfv_f
                        INNER JOIN dbo.custom_field_definitions cfd_f ON cfv_f.field_id = cfd_f.id
                        WHERE cfv_f.entity_type = 'customer'
                          AND cfv_f.entity_id = c.id
                          AND cfd_f.field_key = ?
                          AND cfv_f.field_value LIKE ?
                    )
                    """
                )
                params.extend([key, f"%{str(val).strip()}%"])

    where_sql = " AND ".join(where_clauses)

    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.customers c WHERE {where_sql}", params)
    total = count_row["total"] if count_row else 0

    offset = (page - 1) * per_page
    sql = f"""
        SELECT c.id, c.name, c.phone, c.email, c.address, c.status, c.created_by, u.full_name AS creator_name, c.created_at, c.updated_at
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        WHERE {where_sql}
        ORDER BY c.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    page_params = params + [offset, per_page]
    items = fetch_all(conn, sql, page_params)

    # Đính kèm trường tùy chỉnh vào từng đối tượng
    entity_ids = [item["id"] for item in items]
    cf_map = batch_get_custom_field_values(conn, "customer", entity_ids)

    for item in items:
        item["custom_fields"] = cf_map.get(item["id"], {})

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def get_customer(customer_id: int) -> dict[str, Any] | None:
    conn = get_db()
    row = fetch_one(
        conn,
        """
        SELECT c.id, c.name, c.phone, c.email, c.address, c.status, c.created_by, u.full_name AS creator_name, c.created_at, c.updated_at
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        WHERE c.id = ?
        """,
        (customer_id,),
    )
    if not row:
        return None

    cf_map = batch_get_custom_field_values(conn, "customer", [customer_id])
    row["custom_fields"] = cf_map.get(customer_id, {})
    return row


def create_customer(
    name: str,
    phone: str = "",
    email: str = "",
    address: str = "",
    status: str = "Mới",
    created_by: int = 1,
    custom_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("customer_name_empty")

    cf_input = custom_fields or {}
    is_valid, clean_cf, cf_errors = validate_custom_fields("customer", cf_input)
    if not is_valid:
        raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.customers (name, phone, email, address, status, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, phone.strip(), email.strip(), address.strip(), status.strip() or "Mới", created_by, now, now),
    )
    conn.commit()

    new_row = fetch_one(conn, "SELECT MAX(id) AS id FROM dbo.customers WHERE name = ? AND created_by = ?", (name, created_by))
    cid = new_row["id"]

    # Lưu giá trị trường tùy chỉnh
    save_custom_field_values(conn, "customer", cid, clean_cf)
    conn.commit()

    return get_customer(cid)  # type: ignore


def update_customer(
    customer_id: int,
    name: str,
    phone: str = "",
    email: str = "",
    address: str = "",
    status: str = "Mới",
    custom_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = get_customer(customer_id)
    if not existing:
        raise LookupError("customer_not_found")

    name = name.strip()
    if not name:
        raise ValueError("customer_name_empty")

    cf_input = custom_fields or {}
    is_valid, clean_cf, cf_errors = validate_custom_fields("customer", cf_input)
    if not is_valid:
        raise ValueError({"message": "Dữ liệu trường tùy chỉnh không hợp lệ.", "errors": cf_errors})

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.customers
        SET name = ?, phone = ?, email = ?, address = ?, status = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, phone.strip(), email.strip(), address.strip(), status.strip() or "Mới", now, customer_id),
    )

    save_custom_field_values(conn, "customer", customer_id, clean_cf)
    conn.commit()

    return get_customer(customer_id)  # type: ignore


def delete_customer(customer_id: int) -> bool:
    conn = get_db()
    existing = get_customer(customer_id)
    if not existing:
        raise LookupError("customer_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.custom_field_values WHERE entity_type = 'customer' AND entity_id = ?", (customer_id,))
    cur.execute("DELETE FROM dbo.customers WHERE id = ?", (customer_id,))
    conn.commit()
    return True
