"""
app/support_tickets.py — Yêu cầu Hỗ trợ Sau bán & Gắn cờ Rủi ro Rời bỏ (SCRUM-76)
Dành cho Chăm sóc khách hàng & Nhân viên kinh doanh
"""
import time
from typing import Any

from app.custom_fields import batch_get_custom_field_values
from app.db import fetch_all, fetch_one, get_db

VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_support_tickets_tables(conn) -> None:
    """Khởi tạo bảng support_tickets và các cột cờ rủi ro churn_risk trong dbo.customers nếu chưa có"""
    cur = conn.cursor()
    # 1. Thêm cột is_churn_risk và churn_risk_reason vào dbo.customers nếu chưa tồn tại
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'is_churn_risk')
        BEGIN
            ALTER TABLE dbo.customers ADD is_churn_risk BIT NOT NULL DEFAULT 0;
        END
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'churn_risk_reason')
        BEGIN
            ALTER TABLE dbo.customers ADD churn_risk_reason NVARCHAR(500) NULL;
        END
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.customers') AND name = 'last_interaction_at')
        BEGIN
            ALTER TABLE dbo.customers ADD last_interaction_at BIGINT NULL;
        END
        """
    )
    conn.commit()

    # 2. Tạo bảng dbo.support_tickets nếu chưa tồn tại
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'support_tickets' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.support_tickets (
                id INT IDENTITY(1,1) PRIMARY KEY,
                ticket_code VARCHAR(50) NOT NULL UNIQUE,
                customer_id INT NOT NULL,
                title NVARCHAR(255) NOT NULL,
                description NVARCHAR(MAX),
                priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                status VARCHAR(20) NOT NULL DEFAULT 'open',
                assignee_id INT NULL,
                created_by INT NOT NULL,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL,
                CONSTRAINT FK_tickets_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id)
            );
        END
        """
    )
    conn.commit()


def evaluate_and_update_churn_risk(conn, customer_id: int) -> dict[str, Any]:
    """
    Tự động đánh giá và gắn cờ rủi ro rời bỏ (Churn Risk) cho khách hàng (SCRUM-76):
    - Khách có >= 2 yêu cầu hỗ trợ chưa xử lý (open/in_progress) HOẶC có yêu cầu mức độ khẩn cấp ('urgent') -> Gắn cờ rủi ro.
    - Tất cả yêu cầu được giải quyết (resolved/closed) -> Gỡ cờ rủi ro.
    """
    ensure_support_tickets_tables(conn)

    sql = """
        SELECT priority, status FROM dbo.support_tickets
        WHERE customer_id = ? AND status IN ('open', 'in_progress')
    """
    rows = fetch_all(conn, sql, (customer_id,))
    pending_count = len(rows)
    has_urgent = any(r["priority"] == "urgent" for r in rows)

    is_risk = False
    reason = None

    if has_urgent and pending_count > 0:
        is_risk = True
        reason = f"Có yêu cầu hỗ trợ KHẨN CẤP chưa được xử lý (Tổng số yêu cầu chưa xong: {pending_count})."
    elif pending_count >= 2:
        is_risk = True
        reason = f"Khách hàng có {pending_count} yêu cầu hỗ trợ tồn đọng chưa được giải quyết."

    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.customers
        SET is_churn_risk = ?, churn_risk_reason = ?, updated_at = ?
        WHERE id = ?
        """,
        (1 if is_risk else 0, reason, _now_ms(), customer_id),
    )
    conn.commit()

    return {"is_churn_risk": is_risk, "churn_risk_reason": reason}


# ─── Ticket Management CRUD ──────────────────────────────────────────────────

def list_support_tickets(
    customer_id: int | None = None,
    status: str = "",
    priority: str = "",
    assignee_id: int | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    conn = get_db()
    ensure_support_tickets_tables(conn)

    where_clauses = ["1=1"]
    params: list[Any] = []

    if customer_id:
        where_clauses.append("t.customer_id = ?")
        params.append(customer_id)

    if status and status.strip():
        where_clauses.append("t.status = ?")
        params.append(status.strip().lower())

    if priority and priority.strip():
        where_clauses.append("t.priority = ?")
        params.append(priority.strip().lower())

    if assignee_id:
        where_clauses.append("t.assignee_id = ?")
        params.append(assignee_id)

    where_sql = " AND ".join(where_clauses)
    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.support_tickets t WHERE {where_sql}", params)
    total = count_row["total"] if count_row else 0

    offset = max(0, (page - 1) * per_page)
    sql = f"""
        SELECT t.id, t.ticket_code, t.customer_id, c.name AS customer_name,
               t.title, t.description, t.priority, t.status, t.assignee_id,
               u_ass.full_name AS assignee_name, t.created_by, u_cre.full_name AS creator_name,
               t.created_at, t.updated_at
        FROM dbo.support_tickets t
        INNER JOIN dbo.customers c ON t.customer_id = c.id
        LEFT JOIN dbo.users u_ass ON t.assignee_id = u_ass.id
        LEFT JOIN dbo.users u_cre ON t.created_by = u_cre.id
        WHERE {where_sql}
        ORDER BY t.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = fetch_all(conn, sql, params + [offset, max(1, per_page)])

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def get_support_ticket(ticket_id: int) -> dict[str, Any] | None:
    conn = get_db()
    ensure_support_tickets_tables(conn)
    row = fetch_one(
        conn,
        """
        SELECT t.id, t.ticket_code, t.customer_id, c.name AS customer_name,
               t.title, t.description, t.priority, t.status, t.assignee_id,
               u_ass.full_name AS assignee_name, t.created_by, u_cre.full_name AS creator_name,
               t.created_at, t.updated_at
        FROM dbo.support_tickets t
        INNER JOIN dbo.customers c ON t.customer_id = c.id
        LEFT JOIN dbo.users u_ass ON t.assignee_id = u_ass.id
        LEFT JOIN dbo.users u_cre ON t.created_by = u_cre.id
        WHERE t.id = ?
        """,
        (ticket_id,),
    )
    return row


def create_support_ticket(
    customer_id: int,
    title: str,
    description: str = "",
    priority: str = "medium",
    status: str = "open",
    assignee_id: int | None = None,
    created_by: int = 1,
) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise ValueError("ticket_title_empty")

    priority = priority.strip().lower()
    if priority not in VALID_PRIORITIES:
        raise ValueError("priority_invalid")

    status = status.strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError("status_invalid")

    conn = get_db()
    ensure_support_tickets_tables(conn)

    # Kiểm tra tồn tại khách hàng
    cust = fetch_one(conn, "SELECT id FROM dbo.customers WHERE id = ?", (customer_id,))
    if not cust:
        raise LookupError("customer_not_found")

    now = _now_ms()
    ticket_code = f"TK-{int(time.time() * 1000) % 1000000:06d}"

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.support_tickets
        (ticket_code, customer_id, title, description, priority, status, assignee_id, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_code, customer_id, title, description.strip(), priority, status, assignee_id, created_by, now, now),
    )
    conn.commit()

    # Đánh giá lại cờ rủi ro rời bỏ rời bỏ cho khách hàng
    evaluate_and_update_churn_risk(conn, customer_id)

    new_row = fetch_one(conn, "SELECT MAX(id) AS id FROM dbo.support_tickets WHERE ticket_code = ?", (ticket_code,))
    return get_support_ticket(new_row["id"])  # type: ignore


def update_support_ticket(
    ticket_id: int,
    title: str,
    description: str = "",
    priority: str = "medium",
    status: str = "open",
    assignee_id: int | None = None,
) -> dict[str, Any]:
    existing = get_support_ticket(ticket_id)
    if not existing:
        raise LookupError("ticket_not_found")

    title = title.strip()
    if not title:
        raise ValueError("ticket_title_empty")

    priority = priority.strip().lower()
    if priority not in VALID_PRIORITIES:
        raise ValueError("priority_invalid")

    status = status.strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError("status_invalid")

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.support_tickets
        SET title = ?, description = ?, priority = ?, status = ?, assignee_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (title, description.strip(), priority, status, assignee_id, now, ticket_id),
    )
    conn.commit()

    # Tự động cập nhật cờ rủi ro rời bỏ sau khi đổi trạng thái ticket
    evaluate_and_update_churn_risk(conn, existing["customer_id"])

    return get_support_ticket(ticket_id)  # type: ignore


def delete_support_ticket(ticket_id: int) -> bool:
    existing = get_support_ticket(ticket_id)
    if not existing:
        raise LookupError("ticket_not_found")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.support_tickets WHERE id = ?", (ticket_id,))
    conn.commit()

    # Tự động cập nhật lại cờ rủi ro rời bỏ
    evaluate_and_update_churn_risk(conn, existing["customer_id"])
    return True


# ─── Customer 360 View & Alerts ──────────────────────────────────────────────

def get_customer_360(customer_id: int) -> dict[str, Any] | None:
    """
    Góc nhìn 360 độ về Khách hàng (SCRUM-76):
    - Đầy đủ thông tin khách hàng & Trường tùy chỉnh.
    - Cờ cảnh báo Rủi ro rời bỏ (is_churn_risk & reason) gửi cho NVKD phụ trách.
    - Lịch sử Yêu cầu Hỗ trợ (Tickets).
    - Danh sách Cơ hội kinh doanh liên quan.
    """
    conn = get_db()
    ensure_support_tickets_tables(conn)

    cust = fetch_one(
        conn,
        """
        SELECT c.id, c.name, c.phone, c.email, c.address, c.status, c.is_churn_risk, c.churn_risk_reason,
               c.last_interaction_at, c.created_by, u.full_name AS owner_name, c.created_at, c.updated_at
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        WHERE c.id = ?
        """,
        (customer_id,),
    )
    if not cust:
        return None

    cust["is_churn_risk"] = bool(cust.get("is_churn_risk", False))

    # Gắn Custom Fields
    cf_map = batch_get_custom_field_values(conn, "customer", [customer_id])
    cust["custom_fields"] = cf_map.get(customer_id, {})

    # Lấy danh sách support tickets
    tickets = fetch_all(
        conn,
        """
        SELECT t.id, t.ticket_code, t.title, t.priority, t.status, t.assignee_id, u.full_name AS assignee_name, t.created_at
        FROM dbo.support_tickets t
        LEFT JOIN dbo.users u ON t.assignee_id = u.id
        WHERE t.customer_id = ?
        ORDER BY t.id DESC
        """,
        (customer_id,),
    )
    cust["support_tickets"] = tickets
    cust["pending_tickets_count"] = sum(1 for t in tickets if t["status"] in ("open", "in_progress"))

    # Lấy danh sách Cơ hội liên quan
    opps = fetch_all(
        conn,
        """
        SELECT o.id, o.title, o.value, o.stage, o.stage_key, o.win_probability, o.expected_close_date, o.created_at
        FROM dbo.opportunities o
        WHERE o.customer_id = ?
        ORDER BY o.id DESC
        """,
        (customer_id,),
    )
    cust["opportunities"] = opps
    cust["total_opportunity_value"] = sum(float(o["value"] or 0) for o in opps)

    # Cảnh báo rủi ro rời bỏ dành cho Nhân viên Kinh doanh phụ trách
    if cust["is_churn_risk"]:
        cust["alert"] = {
            "level": "warning",
            "message": f"CẢNH BÁO RỦI RO RỜI BỎ: {cust['churn_risk_reason']}",
            "suggested_action": "Liên hệ ngay với khách hàng để xử lý triệt để các khiếu nại/yêu cầu tồn đọng.",
        }
    else:
        cust["alert"] = None

    return cust


def list_churn_risk_alerts() -> list[dict[str, Any]]:
    """Trả về danh sách tất cả các khách hàng bị cảnh báo Rủi ro rời bỏ để gửi thông báo cho NVKD phụ trách"""
    conn = get_db()
    ensure_support_tickets_tables(conn)

    sql = """
        SELECT c.id, c.name, c.phone, c.email, c.status, c.is_churn_risk, c.churn_risk_reason,
               c.created_by AS owner_id, u.full_name AS owner_name, c.updated_at
        FROM dbo.customers c
        LEFT JOIN dbo.users u ON c.created_by = u.id
        WHERE c.is_churn_risk = 1
        ORDER BY c.updated_at DESC
    """
    rows = fetch_all(conn, sql)
    for r in rows:
        r["is_churn_risk"] = True
    return rows
