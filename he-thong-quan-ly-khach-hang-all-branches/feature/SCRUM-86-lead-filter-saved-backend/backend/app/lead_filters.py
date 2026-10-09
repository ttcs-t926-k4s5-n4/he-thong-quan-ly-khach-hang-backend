"""
app/lead_filters.py — Bộ lọc Lead nâng cao & Bộ lọc lưu sẵn (SCRUM-86)

Nhân viên kinh doanh có thể:
  1. Lọc lead theo: trạng thái, nguồn, phân loại (nóng/ấm/lạnh), người phụ trách, khoảng thời gian
  2. Lead quá SLA tự động hiển thị nổi bật (sla_status = 'breached')
  3. Lưu và đặt tên bộ lọc hay dùng (saved filters)
  4. Áp dụng lại bộ lọc đã lưu chỉ bằng một cú nhấp chuột
"""
import json
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db
from app.leads import (
    _compute_sla_status,
    ensure_leads_tables,
)


def _now_ms() -> int:
    return int(time.time() * 1000)


# ─── Saved Lead Filters (tương tự SCRUM-75 nhưng cho leads) ──────────────────


def ensure_lead_saved_filters_table(conn) -> None:
    """Bảng bộ lọc lead đã lưu."""
    cur = conn.cursor()
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'lead_saved_filters' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.lead_saved_filters (
                id              INT             IDENTITY(1,1) PRIMARY KEY,
                user_id         INT             NOT NULL,
                name            NVARCHAR(255)   NOT NULL,
                criteria_json   NVARCHAR(MAX)   NOT NULL,
                created_at      BIGINT          NOT NULL,
                updated_at      BIGINT          NOT NULL
            );
        END
        """
    )
    conn.commit()


def search_and_filter_leads(
    q: str = "",
    status: str = "",
    source: str = "",
    classification: str = "",
    assigned_to: int | None = None,
    date_from: int | None = None,
    date_to: int | None = None,
    sla_breached_only: bool = False,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    """
    Tìm kiếm và lọc lead theo nhiều điều kiện (SCRUM-86):
    - Lọc theo trạng thái, nguồn, phân loại nóng/ấm/lạnh, người phụ trách, khoảng thời gian.
    - Lead quá SLA được đánh dấu sla_status = 'breached' để frontend hiển thị nổi bật.
    - Hỗ trợ phân trang và sắp xếp linh hoạt.
    """
    conn = get_db()
    ensure_leads_tables(conn)

    now = _now_ms()
    where_clauses = ["1=1"]
    params: list[Any] = []

    # 1. Tìm kiếm toàn văn
    if q and q.strip():
        kw = f"%{q.strip()}%"
        where_clauses.append(
            "(l.full_name LIKE ? OR l.email LIKE ? OR l.phone LIKE ? OR l.company LIKE ?)"
        )
        params.extend([kw, kw, kw, kw])

    # 2. Lọc theo trạng thái
    if status and status.strip():
        where_clauses.append("l.status = ?")
        params.append(status.strip())

    # 3. Lọc theo nguồn
    if source and source.strip():
        where_clauses.append("l.source LIKE ?")
        params.append(f"%{source.strip()}%")

    # 4. Lọc theo phân loại nóng/ấm/lạnh
    if classification and classification.strip().lower() in {"hot", "warm", "cold"}:
        where_clauses.append("l.classification = ?")
        params.append(classification.strip().lower())

    # 5. Lọc theo người phụ trách
    if assigned_to is not None and assigned_to > 0:
        where_clauses.append("l.assigned_to = ?")
        params.append(assigned_to)

    # 6. Lọc theo khoảng thời gian tạo
    if date_from is not None:
        where_clauses.append("l.created_at >= ?")
        params.append(date_from)

    if date_to is not None:
        where_clauses.append("l.created_at <= ?")
        params.append(date_to)

    # 7. Chỉ lấy lead quá SLA
    if sla_breached_only:
        where_clauses.append(
            """
            (l.sla_breached = 1 OR
             (l.sla_deadline_at IS NOT NULL AND l.sla_deadline_at <= ? AND l.status = ?))
            """
        )
        params.extend([now, "Đã phân công"])

    where_sql = " AND ".join(where_clauses)

    count_row = fetch_one(
        conn,
        f"SELECT COUNT(*) AS total FROM dbo.leads l WHERE {where_sql}",
        params,
    )
    total = count_row["total"] if count_row else 0

    allowed_sort = {
        "id": "l.id",
        "created_at": "l.created_at",
        "full_name": "l.full_name",
        "status": "l.status",
        "sla_deadline_at": "l.sla_deadline_at",
        "classification": "l.classification",
    }
    sort_col = allowed_sort.get(sort_by.lower(), "l.created_at")
    sort_dir = "ASC" if order.lower() == "asc" else "DESC"

    offset = max(0, (page - 1) * per_page)
    sql = f"""
        SELECT l.id, l.full_name, l.email, l.phone, l.company, l.source,
               l.classification, l.status, l.assigned_to, l.assigned_at,
               l.sla_deadline_at, l.sla_breached, l.sla_alert_sent,
               l.rejection_reason, l.rejection_count, l.converted_at,
               l.customer_id, l.notes, l.created_by, l.created_at, l.updated_at,
               u_assigned.full_name AS assigned_to_name,
               u_creator.full_name  AS creator_name
        FROM dbo.leads l
        LEFT JOIN dbo.users u_assigned ON l.assigned_to = u_assigned.id
        LEFT JOIN dbo.users u_creator  ON l.created_by  = u_creator.id
        WHERE {where_sql}
        ORDER BY {sort_col} {sort_dir}, l.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = fetch_all(conn, sql, params + [offset, max(1, per_page)])

    # Tính sla_status cho từng lead (hiển thị nổi bật nếu 'breached' hoặc 'warning')
    for item in items:
        item["sla_status"] = _compute_sla_status(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


# ─── CRUD Bộ lọc đã lưu ───────────────────────────────────────────────────────

def list_lead_saved_filters(user_id: int) -> list[dict[str, Any]]:
    """Lấy danh sách bộ lọc lead đã lưu của user."""
    conn = get_db()
    ensure_lead_saved_filters_table(conn)
    rows = fetch_all(
        conn,
        """
        SELECT id, user_id, name, criteria_json, created_at, updated_at
        FROM dbo.lead_saved_filters
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    for r in rows:
        try:
            r["criteria"] = json.loads(r["criteria_json"])
        except Exception:
            r["criteria"] = {}
    return rows


def get_lead_saved_filter(filter_id: int, user_id: int) -> dict[str, Any] | None:
    """Lấy bộ lọc lead đã lưu theo id."""
    conn = get_db()
    ensure_lead_saved_filters_table(conn)
    row = fetch_one(
        conn,
        """
        SELECT id, user_id, name, criteria_json, created_at, updated_at
        FROM dbo.lead_saved_filters
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


def create_lead_saved_filter(
    user_id: int,
    name: str,
    criteria: dict[str, Any],
) -> dict[str, Any]:
    """Lưu bộ lọc lead mới với tên gợi nhớ."""
    name = name.strip()
    if not name:
        raise ValueError("filter_name_empty")
    if not isinstance(criteria, dict):
        raise ValueError("criteria_invalid")

    criteria_json = json.dumps(criteria, ensure_ascii=False)
    conn = get_db()
    ensure_lead_saved_filters_table(conn)

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.lead_saved_filters (user_id, name, criteria_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, name, criteria_json, now, now),
    )
    conn.commit()

    new_row = fetch_one(
        conn,
        "SELECT MAX(id) AS id FROM dbo.lead_saved_filters WHERE user_id = ? AND name = ?",
        (user_id, name),
    )
    return get_lead_saved_filter(new_row["id"], user_id)  # type: ignore


def update_lead_saved_filter(
    filter_id: int,
    user_id: int,
    name: str,
    criteria: dict[str, Any],
) -> dict[str, Any]:
    """Cập nhật tên/tiêu chí bộ lọc lead đã lưu."""
    existing = get_lead_saved_filter(filter_id, user_id)
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
        UPDATE dbo.lead_saved_filters
        SET name = ?, criteria_json = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, criteria_json, now, filter_id, user_id),
    )
    conn.commit()
    return get_lead_saved_filter(filter_id, user_id)  # type: ignore


def delete_lead_saved_filter(filter_id: int, user_id: int) -> bool:
    """Xóa bộ lọc lead đã lưu."""
    existing = get_lead_saved_filter(filter_id, user_id)
    if not existing:
        raise LookupError("filter_not_found")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM dbo.lead_saved_filters WHERE id = ? AND user_id = ?",
        (filter_id, user_id),
    )
    conn.commit()
    return True


def apply_lead_saved_filter(
    filter_id: int,
    user_id: int,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """
    Áp dụng bộ lọc đã lưu (load criteria và gọi search_and_filter_leads).
    Cho phép nhân viên mở máy buổi sáng là biết ngay hôm nay cần gọi ai.
    """
    sf = get_lead_saved_filter(filter_id, user_id)
    if not sf:
        raise LookupError("filter_not_found")

    criteria = sf.get("criteria", {})
    return search_and_filter_leads(
        q=criteria.get("q", ""),
        status=criteria.get("status", ""),
        source=criteria.get("source", ""),
        classification=criteria.get("classification", ""),
        assigned_to=criteria.get("assigned_to"),
        date_from=criteria.get("date_from"),
        date_to=criteria.get("date_to"),
        sla_breached_only=bool(criteria.get("sla_breached_only", False)),
        page=page,
        per_page=per_page,
        sort_by=criteria.get("sort_by", "created_at"),
        order=criteria.get("order", "desc"),
    )
