"""
app/customer_filters.py — Bộ lọc nâng cao & Quản lý Bộ lọc đã lưu cho Khách hàng (SCRUM-75)
Dành cho Nhân viên kinh doanh & Chăm sóc khách hàng
"""
import json
import time
from typing import Any

from app.custom_fields import batch_get_custom_field_values
from app.db import fetch_all, fetch_one, get_db


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_saved_filters_table(conn) -> None:
    """Tự động khởi tạo bảng dbo.saved_filters nếu chưa tồn tại trong Database"""
    cur = conn.cursor()
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'saved_filters' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.saved_filters (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                name NVARCHAR(255) NOT NULL,
                filter_target VARCHAR(50) NOT NULL DEFAULT 'customer',
                criteria_json NVARCHAR(MAX) NOT NULL,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL
            );
        END
        """
    )
    conn.commit()


def search_and_filter_customers(
    q: str = "",
    status: str = "",
    industry: str = "",
    scale: str = "",
    region: str = "",
    owner_id: int | None = None,
    cf_filters: dict[str, Any] | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    """
    Tìm kiếm và lọc khách hàng theo nhiều điều kiện (SCRUM-75):
    - Lọc theo Trạng thái, Ngành nghề, Quy mô, Khu vực, Người sở hữu (owner_id).
    - Tìm kiếm theo Tên, Mã số thuế, Số điện thoại.
    - Phân trang và Sắp xếp kết quả linh hoạt.
    """
    conn = get_db()
    where_clauses = ["1=1"]
    params: list[Any] = []

    # 1. Tìm kiếm đa trường (Tên, Mã số thuế, Số điện thoại)
    if q and q.strip():
        kw = f"%{q.strip()}%"
        # Tìm trong các cột tiêu chuẩn của customers VÀ trong custom field 'tax_code'
        where_clauses.append(
            """
            (
                c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ? OR c.address LIKE ?
                OR EXISTS (
                    SELECT 1 FROM dbo.custom_field_values cfv_q
                    INNER JOIN dbo.custom_field_definitions cfd_q ON cfv_q.field_id = cfd_q.id
                    WHERE cfv_q.entity_type = 'customer'
                      AND cfv_q.entity_id = c.id
                      AND cfd_q.field_key = 'tax_code'
                      AND cfv_q.field_value LIKE ?
                )
            )
            """
        )
        params.extend([kw, kw, kw, kw, kw])

    # 2. Lọc theo trạng thái
    if status and status.strip():
        where_clauses.append("c.status = ?")
        params.append(status.strip())

    # 3. Lọc theo Người sở hữu (owner_id / created_by)
    if owner_id is not None and owner_id > 0:
        where_clauses.append("c.created_by = ?")
        params.append(owner_id)

    # 4. Lọc theo Ngành nghề (industry - custom field hoặc address)
    if industry and industry.strip():
        where_clauses.append(
            """
            EXISTS (
                SELECT 1 FROM dbo.custom_field_values cfv_ind
                INNER JOIN dbo.custom_field_definitions cfd_ind ON cfv_ind.field_id = cfd_ind.id
                WHERE cfv_ind.entity_type = 'customer'
                  AND cfv_ind.entity_id = c.id
                  AND cfd_ind.field_key = 'industry'
                  AND cfv_ind.field_value LIKE ?
            )
            """
        )
        params.append(f"%{industry.strip()}%")

    # 5. Lọc theo Quy mô (scale / company_size)
    if scale and scale.strip():
        where_clauses.append(
            """
            EXISTS (
                SELECT 1 FROM dbo.custom_field_values cfv_sc
                INNER JOIN dbo.custom_field_definitions cfd_sc ON cfv_sc.field_id = cfd_sc.id
                WHERE cfv_sc.entity_type = 'customer'
                  AND cfv_sc.entity_id = c.id
                  AND (cfd_sc.field_key = 'company_size' OR cfd_sc.field_key = 'scale')
                  AND cfv_sc.field_value LIKE ?
            )
            """
        )
        params.append(f"%{scale.strip()}%")

    # 6. Lọc theo Khu vực (region / city / address)
    if region and region.strip():
        reg_kw = f"%{region.strip()}%"
        where_clauses.append(
            """
            (
                c.address LIKE ? OR EXISTS (
                    SELECT 1 FROM dbo.custom_field_values cfv_reg
                    INNER JOIN dbo.custom_field_definitions cfd_reg ON cfv_reg.field_id = cfd_reg.id
                    WHERE cfv_reg.entity_type = 'customer'
                      AND cfv_reg.entity_id = c.id
                      AND (cfd_reg.field_key = 'region' OR cfd_reg.field_key = 'city')
                      AND cfv_reg.field_value LIKE ?
                )
            )
            """
        )
        params.extend([reg_kw, reg_kw])

    # 7. Lọc bổ sung theo custom fields khác nếu có
    if cf_filters:
        for key, val in cf_filters.items():
            if val is not None and str(val).strip() != "":
                where_clauses.append(
                    """
                    EXISTS (
                        SELECT 1 FROM dbo.custom_field_values cfv_dyn
                        INNER JOIN dbo.custom_field_definitions cfd_dyn ON cfv_dyn.field_id = cfd_dyn.id
                        WHERE cfv_dyn.entity_type = 'customer'
                          AND cfv_dyn.entity_id = c.id
                          AND cfd_dyn.field_key = ?
                          AND cfv_dyn.field_value LIKE ?
                    )
                    """
                )
                params.extend([key, f"%{str(val).strip()}%"])

    where_sql = " AND ".join(where_clauses)

    # Đếm tổng số kết quả
    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.customers c WHERE {where_sql}", params)
    total = count_row["total"] if count_row else 0

    # Phân trang & Sắp xếp
    allowed_sort_fields = {"id": "c.id", "name": "c.name", "created_at": "c.created_at", "status": "c.status"}
    sort_column = allowed_sort_fields.get(sort_by.lower(), "c.created_at")
    sort_order = "ASC" if order.lower() == "asc" else "DESC"

    offset = max(0, (page - 1) * per_page)
    sql = f"""
        SELECT c.id, c.name, c.phone, c.email, c.address, c.status, c.created_by,
               u.full_name AS creator_name, c.created_at, c.updated_at
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_order}, c.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    page_params = params + [offset, max(1, per_page)]
    items = fetch_all(conn, sql, page_params)

    # Gắn thông tin Custom Fields vào từng khách hàng
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


# ─── Quản lý Bộ Lọc Đã Lưu (Saved Filters) ───────────────────────────────────

def list_saved_filters(user_id: int, filter_target: str = "customer") -> list[dict[str, Any]]:
    conn = get_db()
    ensure_saved_filters_table(conn)
    sql = """
        SELECT id, user_id, name, filter_target, criteria_json, created_at, updated_at
        FROM dbo.saved_filters
        WHERE user_id = ? AND filter_target = ?
        ORDER BY id DESC
    """
    rows = fetch_all(conn, sql, (user_id, filter_target))
    for r in rows:
        try:
            r["criteria"] = json.loads(r["criteria_json"])
        except Exception:
            r["criteria"] = {}
    return rows


def get_saved_filter(filter_id: int, user_id: int) -> dict[str, Any] | None:
    conn = get_db()
    ensure_saved_filters_table(conn)
    row = fetch_one(
        conn,
        """
        SELECT id, user_id, name, filter_target, criteria_json, created_at, updated_at
        FROM dbo.saved_filters
        WHERE id = ? AND user_id = ?
        """,
        (filter_id, user_id),
    )
    if not row:
        return None
    try:
        row["criteria"] = json.loads(row["criteria_json"])
    except Exception:
        row["criteria"] = {}
    return row


def create_saved_filter(
    user_id: int,
    name: str,
    criteria: dict[str, Any],
    filter_target: str = "customer",
) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("filter_name_empty")

    if not isinstance(criteria, dict):
        raise ValueError("criteria_invalid")

    criteria_json = json.dumps(criteria, ensure_ascii=False)
    conn = get_db()
    ensure_saved_filters_table(conn)

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.saved_filters (user_id, name, filter_target, criteria_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, name, filter_target.strip().lower(), criteria_json, now, now),
    )
    conn.commit()

    new_row = fetch_one(
        conn,
        "SELECT MAX(id) AS id FROM dbo.saved_filters WHERE user_id = ? AND name = ?",
        (user_id, name),
    )
    return get_saved_filter(new_row["id"], user_id)  # type: ignore


def update_saved_filter(
    filter_id: int,
    user_id: int,
    name: str,
    criteria: dict[str, Any],
) -> dict[str, Any]:
    existing = get_saved_filter(filter_id, user_id)
    if not existing:
        raise LookupError("filter_not_found")

    name = name.strip()
    if not name:
        raise ValueError("filter_name_empty")

    if not isinstance(criteria, dict):
        raise ValueError("criteria_invalid")

    criteria_json = json.dumps(criteria, ensure_ascii=False)
    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.saved_filters
        SET name = ?, criteria_json = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, criteria_json, now, filter_id, user_id),
    )
    conn.commit()
    return get_saved_filter(filter_id, user_id)  # type: ignore


def delete_saved_filter(filter_id: int, user_id: int) -> bool:
    existing = get_saved_filter(filter_id, user_id)
    if not existing:
        raise LookupError("filter_not_found")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.saved_filters WHERE id = ? AND user_id = ?", (filter_id, user_id))
    conn.commit()
    return True
