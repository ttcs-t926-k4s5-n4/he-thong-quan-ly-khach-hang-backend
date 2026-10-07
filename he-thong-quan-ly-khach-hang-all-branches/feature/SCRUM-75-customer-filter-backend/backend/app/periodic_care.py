"""
app/periodic_care.py — Danh sách Khách hàng Cần chăm sóc Định kỳ & Đánh dấu Tương tác (SCRUM-77)
Dành cho Bộ phận Chăm sóc khách hàng & Kinh doanh
"""
import time
from typing import Any

from app.custom_fields import batch_get_custom_field_values
from app.db import fetch_all, fetch_one, get_db

MS_PER_DAY = 24 * 3600 * 1000


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_periodic_care_tables(conn) -> None:
    """Đảm bảo bảng customer_interactions và cột last_interaction_at trong dbo.customers đã tồn tại"""
    cur = conn.cursor()
    # 1. Thêm cột last_interaction_at nếu chưa tồn tại
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'last_interaction_at')
        BEGIN
            ALTER TABLE dbo.customers ADD last_interaction_at BIGINT NULL;
        END
        """
    )
    conn.commit()

    # 2. Tạo bảng dbo.customer_interactions nếu chưa có
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'customer_interactions' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.customer_interactions (
                id INT IDENTITY(1,1) PRIMARY KEY,
                customer_id INT NOT NULL,
                interaction_type NVARCHAR(50) NOT NULL DEFAULT N'Gọi điện chăm sóc',
                notes NVARCHAR(MAX),
                created_by INT NOT NULL,
                created_at BIGINT NOT NULL,
                CONSTRAINT FK_interactions_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id)
            );
        END
        """
    )
    conn.commit()


def list_periodic_care_customers(
    days: int = 30,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """
    Lấy danh sách khách hàng cần chăm sóc định kỳ (SCRUM-77):
    - Khách chưa có tương tác nào trong N ngày (days=N).
    - Sắp xếp giảm dần theo tổng giá trị hợp đồng/cơ hội (`contract_value` DESC).
    """
    conn = get_db()
    ensure_periodic_care_tables(conn)

    now = _now_ms()
    threshold_ms = now - (max(1, days) * MS_PER_DAY)

    # Lấy khách hàng chưa tương tác trong N ngày
    sql = """
        SELECT c.id, c.name, c.phone, c.email, c.address, c.status, c.last_interaction_at,
               c.created_by, u.full_name AS owner_name, c.created_at,
               ISNULL(SUM(o.value), 0) AS total_contract_value
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        LEFT JOIN dbo.opportunities o ON c.id = o.customer_id
        WHERE ISNULL(c.last_interaction_at, c.created_at) <= ?
        GROUP BY c.id, c.name, c.phone, c.email, c.address, c.status, c.last_interaction_at,
                 c.created_by, u.full_name, c.created_at
        ORDER BY total_contract_value DESC, c.id DESC
    """
    rows = fetch_all(conn, sql, (threshold_ms,))

    # Phân trang bằng Python list slice
    total = len(rows)
    offset = max(0, (page - 1) * per_page)
    paged_items = rows[offset : offset + max(1, per_page)]

    # Gắn thêm số ngày chưa tương tác & Custom Fields
    entity_ids = [item["id"] for item in paged_items]
    cf_map = batch_get_custom_field_values(conn, "customer", entity_ids)

    for item in paged_items:
        last_time = item["last_interaction_at"] or item["created_at"]
        days_inactive = int((now - last_time) / MS_PER_DAY)
        item["days_without_interaction"] = days_inactive
        item["contract_value"] = float(item["total_contract_value"])
        item["custom_fields"] = cf_map.get(item["id"], {})

    return {
        "items": paged_items,
        "total": total,
        "days_threshold": days,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def record_customer_interaction(
    customer_id: int,
    interaction_type: str = "Gọi điện chăm sóc",
    notes: str = "",
    created_by: int = 1,
) -> dict[str, Any]:
    """
    Đánh dấu đã liên hệ / Ghi nhận tương tác chăm sóc định kỳ cho Khách hàng (SCRUM-77):
    - Ghi nhận lịch sử tương tác vào dbo.customer_interactions.
    - Cập nhật last_interaction_at = now() cho khách hàng.
    """
    conn = get_db()
    ensure_periodic_care_tables(conn)

    cust = fetch_one(conn, "SELECT id, name FROM dbo.customers WHERE id = ?", (customer_id,))
    if not cust:
        raise LookupError("customer_not_found")

    interaction_type = interaction_type.strip() or "Gọi điện chăm sóc"
    now = _now_ms()
    cur = conn.cursor()

    # 1. Thêm bản ghi tương tác
    cur.execute(
        """
        INSERT INTO dbo.customer_interactions (customer_id, interaction_type, notes, created_by, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (customer_id, interaction_type, notes.strip(), created_by, now),
    )

    # 2. Cập nhật thời điểm tương tác gần nhất
    cur.execute(
        """
        UPDATE dbo.customers
        SET last_interaction_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, now, customer_id),
    )
    conn.commit()

    new_row = fetch_one(conn, "SELECT MAX(id) AS id FROM dbo.customer_interactions WHERE customer_id = ?", (customer_id,))

    return {
        "id": new_row["id"],
        "customer_id": customer_id,
        "customer_name": cust["name"],
        "interaction_type": interaction_type,
        "notes": notes.strip(),
        "created_by": created_by,
        "created_at": now,
        "last_interaction_at": now,
    }


def list_customer_interactions(customer_id: int) -> list[dict[str, Any]]:
    """Lấy danh sách lịch sử tương tác chăm sóc của 1 khách hàng"""
    conn = get_db()
    ensure_periodic_care_tables(conn)

    sql = """
        SELECT i.id, i.customer_id, i.interaction_type, i.notes, i.created_by,
               u.full_name AS creator_name, i.created_at
        FROM dbo.customer_interactions i
        LEFT JOIN dbo.users u ON i.created_by = u.id
        WHERE i.customer_id = ?
        ORDER BY i.id DESC
    """
    return fetch_all(conn, sql, (customer_id,))
