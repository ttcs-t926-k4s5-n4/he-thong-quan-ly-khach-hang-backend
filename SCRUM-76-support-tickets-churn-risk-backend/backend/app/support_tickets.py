"""
app/support_tickets.py ΓÇö Y├¬u cß║ºu Hß╗ù trß╗ú Sau b├ín & Gß║»n cß╗¥ Rß╗ºi ro Rß╗¥i bß╗Å (SCRUM-76)
D├ánh cho Ch─âm s├│c kh├ích h├áng & Nh├ón vi├¬n kinh doanh
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
    """Khß╗ƒi tß║ío bß║úng support_tickets v├á c├íc cß╗Öt cß╗¥ rß╗ºi ro churn_risk trong dbo.customers nß║┐u ch╞░a c├│"""
    cur = conn.cursor()
    # 1. Th├¬m cß╗Öt is_churn_risk v├á churn_risk_reason v├áo dbo.customers nß║┐u ch╞░a tß╗ôn tß║íi
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

    # 2. Tß║ío bß║úng dbo.support_tickets nß║┐u ch╞░a tß╗ôn tß║íi
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
    Tß╗▒ ─æß╗Öng ─æ├ính gi├í v├á gß║»n cß╗¥ rß╗ºi ro rß╗¥i bß╗Å (Churn Risk) cho kh├ích h├áng (SCRUM-76):
    - Kh├ích c├│ >= 2 y├¬u cß║ºu hß╗ù trß╗ú ch╞░a xß╗¡ l├╜ (open/in_progress) HOß║╢C c├│ y├¬u cß║ºu mß╗⌐c ─æß╗Ö khß║⌐n cß║Ñp ('urgent') -> Gß║»n cß╗¥ rß╗ºi ro.
    - Tß║Ñt cß║ú y├¬u cß║ºu ─æ╞░ß╗úc giß║úi quyß║┐t (resolved/closed) -> Gß╗í cß╗¥ rß╗ºi ro.
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
        reason = f"C├│ y├¬u cß║ºu hß╗ù trß╗ú KHß║¿N Cß║ñP ch╞░a ─æ╞░ß╗úc xß╗¡ l├╜ (Tß╗òng sß╗æ y├¬u cß║ºu ch╞░a xong: {pending_count})."
    elif pending_count >= 2:
        is_risk = True
        reason = f"Kh├ích h├áng c├│ {pending_count} y├¬u cß║ºu hß╗ù trß╗ú tß╗ôn ─æß╗ìng ch╞░a ─æ╞░ß╗úc giß║úi quyß║┐t."

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


# ΓöÇΓöÇΓöÇ Ticket Management CRUD ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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

    # Kiß╗âm tra tß╗ôn tß║íi kh├ích h├áng
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

    # ─É├ính gi├í lß║íi cß╗¥ rß╗ºi ro rß╗¥i bß╗Å rß╗¥i bß╗Å cho kh├ích h├áng
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

    # Tß╗▒ ─æß╗Öng cß║¡p nhß║¡t cß╗¥ rß╗ºi ro rß╗¥i bß╗Å sau khi ─æß╗òi trß║íng th├íi ticket
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

    # Tß╗▒ ─æß╗Öng cß║¡p nhß║¡t lß║íi cß╗¥ rß╗ºi ro rß╗¥i bß╗Å
    evaluate_and_update_churn_risk(conn, existing["customer_id"])
    return True


# ΓöÇΓöÇΓöÇ Customer 360 View & Alerts ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def get_customer_360(customer_id: int) -> dict[str, Any] | None:
    """
    G├│c nh├¼n 360 ─æß╗Ö vß╗ü Kh├ích h├áng (SCRUM-76):
    - ─Éß║ºy ─æß╗º th├┤ng tin kh├ích h├áng & Tr╞░ß╗¥ng t├╣y chß╗ënh.
    - Cß╗¥ cß║únh b├ío Rß╗ºi ro rß╗¥i bß╗Å (is_churn_risk & reason) gß╗¡i cho NVKD phß╗Ñ tr├ích.
    - Lß╗ïch sß╗¡ Y├¬u cß║ºu Hß╗ù trß╗ú (Tickets).
    - Danh s├ích C╞í hß╗Öi kinh doanh li├¬n quan.
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

    # Gß║»n Custom Fields
    cf_map = batch_get_custom_field_values(conn, "customer", [customer_id])
    cust["custom_fields"] = cf_map.get(customer_id, {})

    # Lß║Ñy danh s├ích support tickets
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

    # Lß║Ñy danh s├ích C╞í hß╗Öi li├¬n quan
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

    # Cß║únh b├ío rß╗ºi ro rß╗¥i bß╗Å d├ánh cho Nh├ón vi├¬n Kinh doanh phß╗Ñ tr├ích
    if cust["is_churn_risk"]:
        cust["alert"] = {
            "level": "warning",
            "message": f"Cß║óNH B├üO Rß╗ªI RO Rß╗£I Bß╗Ä: {cust['churn_risk_reason']}",
            "suggested_action": "Li├¬n hß╗ç ngay vß╗¢i kh├ích h├áng ─æß╗â xß╗¡ l├╜ triß╗çt ─æß╗â c├íc khiß║┐u nß║íi/y├¬u cß║ºu tß╗ôn ─æß╗ìng.",
        }
    else:
        cust["alert"] = None

    return cust


def list_churn_risk_alerts() -> list[dict[str, Any]]:
    """Trß║ú vß╗ü danh s├ích tß║Ñt cß║ú c├íc kh├ích h├áng bß╗ï cß║únh b├ío Rß╗ºi ro rß╗¥i bß╗Å ─æß╗â gß╗¡i th├┤ng b├ío cho NVKD phß╗Ñ tr├ích"""
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
