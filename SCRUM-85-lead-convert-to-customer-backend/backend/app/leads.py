"""
app/leads.py ΓÇö Quß║ún l├╜ Lead: Nhß║¡n/Tß╗½ chß╗æi Lead vß╗¢i r├áng buß╗Öc SLA phß║ún hß╗ôi (SCRUM-84)

Nh├ón vi├¬n kinh doanh c├│ thß╗â:
  1. Nhß║¡n lead ─æ╞░ß╗úc ph├ón ΓåÆ lead chuyß╗ân sang "─Éang ch─âm s├│c"
  2. Tß╗½ chß╗æi lead (bß║»t buß╗Öc nhß║¡p l├╜ do) ΓåÆ lead quay vß╗ü h├áng chß╗¥ ph├ón bß╗ò
  3. Qu├í SLA m├á ch╞░a li├¬n hß╗ç ΓåÆ lead gß║»n cß╗¥ sla_breached=True v├á b├ío tr╞░ß╗ƒng nh├│m
"""
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db

# Trß║íng th├íi lead
LEAD_STATUS_NEW = "Mß╗¢i"                  # Mß╗¢i tß║ío, chß╗¥ ph├ón bß╗ò
LEAD_STATUS_ASSIGNED = "─É├ú ph├ón c├┤ng"   # ─É├ú ph├ón c├┤ng, nh├ón vi├¬n ch╞░a x├íc nhß║¡n
LEAD_STATUS_CARING = "─Éang ch─âm s├│c"   # Nh├ón vi├¬n ─æ├ú nhß║¡n
LEAD_STATUS_WAITING = "Chß╗¥ ph├ón bß╗ò"    # Tß╗½ chß╗æi ΓåÆ quay vß╗ü h├áng chß╗¥
LEAD_STATUS_CONVERTED = "─É├ú chuyß╗ân ─æß╗òi"  # ─É├ú th├ánh kh├ích h├áng
LEAD_STATUS_REJECTED = "─É├ú tß╗½ chß╗æi"     # Cuß╗æi c├╣ng bß╗ï tß╗½ chß╗æi

# SLA mß║╖c ─æß╗ïnh: 3 ng├áy (72 giß╗¥) t├¡nh bß║▒ng milliseconds
SLA_RESPONSE_MS = 3 * 24 * 3600 * 1000


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_leads_tables(conn) -> None:
    """Tß║ío bß║úng dbo.leads v├á bß║úng dbo.lead_activities nß║┐u ch╞░a tß╗ôn tß║íi"""
    cur = conn.cursor()

    # Bß║úng leads ch├¡nh
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'leads' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.leads (
                id                  INT             IDENTITY(1,1) PRIMARY KEY,
                full_name           NVARCHAR(255)   NOT NULL,
                email               NVARCHAR(255)   NULL,
                phone               NVARCHAR(50)    NULL,
                company             NVARCHAR(255)   NULL,
                source              NVARCHAR(100)   NULL,
                classification      VARCHAR(10)     NOT NULL DEFAULT 'cold',
                -- 'hot' = N├│ng | 'warm' = ß║ñm | 'cold' = Lß║ính
                status              NVARCHAR(50)    NOT NULL DEFAULT N'Mß╗¢i',
                -- Mß╗¢i | ─É├ú ph├ón c├┤ng | ─Éang ch─âm s├│c | Chß╗¥ ph├ón bß╗ò | ─É├ú chuyß╗ân ─æß╗òi | ─É├ú tß╗½ chß╗æi
                assigned_to         INT             NULL,
                -- FK ΓåÆ dbo.users.id (nh├ón vi├¬n ─æ╞░ß╗úc ph├ón c├┤ng)
                assigned_at         BIGINT          NULL,
                -- Unix ms khi ph├ón c├┤ng, d├╣ng t├¡nh SLA
                sla_deadline_at     BIGINT          NULL,
                -- Hß║ín ch├│t SLA = assigned_at + 3 ng├áy
                sla_breached        BIT             NOT NULL DEFAULT 0,
                -- 1 nß║┐u ─æ├ú v╞░ß╗út SLA m├á ch╞░a nhß║¡n/tß╗½ chß╗æi
                sla_alert_sent      BIT             NOT NULL DEFAULT 0,
                -- 1 nß║┐u ─æ├ú gß╗¡i cß║únh b├ío SLA cho tr╞░ß╗ƒng nh├│m
                rejection_reason    NVARCHAR(1000)  NULL,
                -- L├╜ do tß╗½ chß╗æi (bß║»t buß╗Öc khi tß╗½ chß╗æi)
                rejection_count     INT             NOT NULL DEFAULT 0,
                -- Sß╗æ lß║ºn ─æ├ú bß╗ï tß╗½ chß╗æi
                converted_at        BIGINT          NULL,
                -- Khi n├áo chuyß╗ân ─æß╗òi th├ánh kh├ích h├áng
                customer_id         INT             NULL,
                -- FK ΓåÆ dbo.customers.id (sau khi chuyß╗ân ─æß╗òi)
                notes               NVARCHAR(MAX)   NULL,
                created_by          INT             NOT NULL,
                created_at          BIGINT          NOT NULL,
                updated_at          BIGINT          NOT NULL
            );
        END
        """
    )
    conn.commit()

    # Bß║úng lß╗ïch sß╗¡ hoß║ít ─æß╗Öng cß╗ºa lead
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'lead_activities' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.lead_activities (
                id              INT             IDENTITY(1,1) PRIMARY KEY,
                lead_id         INT             NOT NULL,
                activity_type   NVARCHAR(100)   NOT NULL,
                -- 'assigned' | 'accepted' | 'rejected' | 'sla_breached' | 'converted' | 'note' | ...
                description     NVARCHAR(MAX)   NULL,
                performed_by    INT             NULL,
                -- FK ΓåÆ dbo.users.id
                created_at      BIGINT          NOT NULL,
                CONSTRAINT FK_lead_activities_lead FOREIGN KEY (lead_id) REFERENCES dbo.leads(id)
            );
        END
        """
    )
    conn.commit()


def _get_lead_raw(conn, lead_id: int) -> dict[str, Any] | None:
    return fetch_one(
        conn,
        """
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
        WHERE l.id = ?
        """,
        (lead_id,),
    )


def get_lead(lead_id: int) -> dict[str, Any] | None:
    conn = get_db()
    ensure_leads_tables(conn)
    row = _get_lead_raw(conn, lead_id)
    if not row:
        return None
    # T├¡nh trß║íng th├íi SLA theo thß╗¥i gian thß╗▒c
    row["sla_status"] = _compute_sla_status(row)
    return row


def _compute_sla_status(lead: dict) -> str:
    """Trß║ú vß╗ü: 'ok' | 'warning' | 'breached' | 'not_assigned'"""
    if not lead.get("assigned_at"):
        return "not_assigned"
    now = _now_ms()
    deadline = lead.get("sla_deadline_at") or 0
    if lead.get("sla_breached"):
        return "breached"
    if deadline > 0 and now >= deadline:
        return "breached"
    # Cß║únh b├ío khi c├▓n d╞░ß╗¢i 8 giß╗¥
    warning_threshold = deadline - 8 * 3600 * 1000
    if now >= warning_threshold:
        return "warning"
    return "ok"


def list_leads(
    q: str = "",
    status: str = "",
    source: str = "",
    classification: str = "",
    assigned_to: int | None = None,
    sla_breached_only: bool = False,
    date_from: int | None = None,
    date_to: int | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict[str, Any]:
    """
    Danh s├ích lead vß╗¢i c├íc bß╗Ö lß╗ìc. (d├╣ng chung cho SCRUM-84 & SCRUM-86)
    """
    conn = get_db()
    ensure_leads_tables(conn)

    where_clauses = ["1=1"]
    params: list[Any] = []

    if q and q.strip():
        kw = f"%{q.strip()}%"
        where_clauses.append(
            "(l.full_name LIKE ? OR l.email LIKE ? OR l.phone LIKE ? OR l.company LIKE ?)"
        )
        params.extend([kw, kw, kw, kw])

    if status and status.strip():
        where_clauses.append("l.status = ?")
        params.append(status.strip())

    if source and source.strip():
        where_clauses.append("l.source LIKE ?")
        params.append(f"%{source.strip()}%")

    if classification and classification.strip():
        where_clauses.append("l.classification = ?")
        params.append(classification.strip().lower())

    if assigned_to is not None and assigned_to > 0:
        where_clauses.append("l.assigned_to = ?")
        params.append(assigned_to)

    if sla_breached_only:
        now = _now_ms()
        where_clauses.append(
            "(l.sla_breached = 1 OR (l.sla_deadline_at IS NOT NULL AND l.sla_deadline_at <= ? AND l.status = ?))"
        )
        params.extend([now, LEAD_STATUS_ASSIGNED])

    if date_from is not None:
        where_clauses.append("l.created_at >= ?")
        params.append(date_from)

    if date_to is not None:
        where_clauses.append("l.created_at <= ?")
        params.append(date_to)

    where_sql = " AND ".join(where_clauses)

    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.leads l WHERE {where_sql}", params)
    total = count_row["total"] if count_row else 0

    allowed_sort = {"id": "l.id", "created_at": "l.created_at", "full_name": "l.full_name",
                    "status": "l.status", "sla_deadline_at": "l.sla_deadline_at"}
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

    now = _now_ms()
    for item in items:
        item["sla_status"] = _compute_sla_status(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def create_lead(
    full_name: str,
    email: str = "",
    phone: str = "",
    company: str = "",
    source: str = "",
    classification: str = "cold",
    notes: str = "",
    created_by: int = 1,
) -> dict[str, Any]:
    """Tß║ío lead mß╗¢i, trß║íng th├íi ban ─æß║ºu l├á 'Mß╗¢i'."""
    full_name = full_name.strip()
    if not full_name:
        raise ValueError("lead_name_empty")
    classification = classification.strip().lower()
    if classification not in {"hot", "warm", "cold"}:
        classification = "cold"

    conn = get_db()
    ensure_leads_tables(conn)
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.leads
            (full_name, email, phone, company, source, classification, status,
             created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            full_name, email.strip(), phone.strip(), company.strip(),
            source.strip(), classification, LEAD_STATUS_NEW,
            created_by, now, now,
        ),
    )
    conn.commit()

    new_row = fetch_one(
        conn,
        "SELECT MAX(id) AS id FROM dbo.leads WHERE created_by = ? AND full_name = ?",
        (created_by, full_name),
    )
    lead_id = new_row["id"]

    _log_activity(conn, lead_id, "created", f"Lead '{full_name}' ─æ╞░ß╗úc tß║ío mß╗¢i.", created_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def assign_lead(lead_id: int, assigned_to: int, assigned_by: int) -> dict[str, Any]:
    """
    Ph├ón c├┤ng lead cho nh├ón vi├¬n kinh doanh.
    - ─Éß║╖t trß║íng th├íi ΓåÆ '─É├ú ph├ón c├┤ng'
    - Ghi nhß║¡n thß╗¥i ─æiß╗âm ph├ón c├┤ng v├á t├¡nh SLA deadline (assigned_at + 3 ng├áy)
    """
    conn = get_db()
    ensure_leads_tables(conn)
    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")
    if lead["status"] == LEAD_STATUS_CONVERTED:
        raise ValueError("lead_already_converted")

    now = _now_ms()
    sla_deadline = now + SLA_RESPONSE_MS
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.leads
        SET assigned_to = ?, assigned_at = ?, sla_deadline_at = ?,
            status = ?, sla_breached = 0, sla_alert_sent = 0, updated_at = ?
        WHERE id = ?
        """,
        (assigned_to, now, sla_deadline, LEAD_STATUS_ASSIGNED, now, lead_id),
    )
    conn.commit()

    assignee = fetch_one(conn, "SELECT full_name FROM dbo.users WHERE id = ?", (assigned_to,))
    name = assignee["full_name"] if assignee else str(assigned_to)
    _log_activity(conn, lead_id, "assigned",
                  f"Lead ─æ╞░ß╗úc ph├ón c├┤ng cho '{name}'. SLA hß║ín ch├│t: {sla_deadline} ms.",
                  assigned_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def accept_lead(lead_id: int, user_id: int) -> dict[str, Any]:
    """
    Nh├ón vi├¬n nhß║¡n lead ΓåÆ lead chuyß╗ân sang '─Éang ch─âm s├│c'.
    Chß╗ë nh├ón vi├¬n ─æ╞░ß╗úc ph├ón c├┤ng mß╗¢i c├│ thß╗â nhß║¡n.
    """
    conn = get_db()
    ensure_leads_tables(conn)
    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")
    if lead["assigned_to"] != user_id:
        raise PermissionError("not_assigned_to_you")
    if lead["status"] not in {LEAD_STATUS_ASSIGNED, LEAD_STATUS_WAITING}:
        raise ValueError("lead_status_not_assignable")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.leads
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (LEAD_STATUS_CARING, now, lead_id),
    )
    conn.commit()

    _log_activity(conn, lead_id, "accepted",
                  f"Nh├ón vi├¬n (id={user_id}) ─æ├ú nhß║¡n lead v├á bß║»t ─æß║ºu ch─âm s├│c.",
                  user_id)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def reject_lead(lead_id: int, user_id: int, reason: str) -> dict[str, Any]:
    """
    Nh├ón vi├¬n tß╗½ chß╗æi lead (bß║»t buß╗Öc phß║úi c├│ l├╜ do).
    Lead quay vß╗ü trß║íng th├íi 'Chß╗¥ ph├ón bß╗ò' v├á t─âng rejection_count.
    Chß╗ë nh├ón vi├¬n ─æ╞░ß╗úc ph├ón c├┤ng mß╗¢i c├│ thß╗â tß╗½ chß╗æi.
    """
    reason = reason.strip()
    if not reason:
        raise ValueError("rejection_reason_required")

    conn = get_db()
    ensure_leads_tables(conn)
    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")
    if lead["assigned_to"] != user_id:
        raise PermissionError("not_assigned_to_you")
    if lead["status"] not in {LEAD_STATUS_ASSIGNED, LEAD_STATUS_CARING}:
        raise ValueError("lead_status_not_rejectable")

    now = _now_ms()
    new_count = (lead["rejection_count"] or 0) + 1
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.leads
        SET status = ?, rejection_reason = ?, rejection_count = ?,
            assigned_to = NULL, assigned_at = NULL, sla_deadline_at = NULL,
            sla_breached = 0, updated_at = ?
        WHERE id = ?
        """,
        (LEAD_STATUS_WAITING, reason, new_count, now, lead_id),
    )
    conn.commit()

    _log_activity(conn, lead_id, "rejected",
                  f"Nh├ón vi├¬n (id={user_id}) tß╗½ chß╗æi lead. L├╜ do: {reason}",
                  user_id)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def check_and_flag_sla_breached_leads(manager_user_id: int | None = None) -> list[dict[str, Any]]:
    """
    Qu├⌐t tß║Ñt cß║ú lead ─æ├ú ph├ón c├┤ng nh╞░ng qu├í SLA deadline m├á ch╞░a ─æ╞░ß╗úc nhß║¡n/tß╗½ chß╗æi.
    ΓåÆ Gß║»n cß╗¥ sla_breached = 1
    ΓåÆ Ghi activity cß║únh b├ío cho tr╞░ß╗ƒng nh├│m

    H├ám n├áy n├¬n ─æ╞░ß╗úc gß╗ìi ─æß╗ïnh kß╗│ (scheduler / cronjob) hoß║╖c khi nh├ón vi├¬n mß╗ƒ danh s├ích lead.
    Trß║ú vß╗ü danh s├ích lead vß╗½a bß╗ï gß║»n cß╗¥ SLA vi phß║ím.
    """
    conn = get_db()
    ensure_leads_tables(conn)
    now = _now_ms()

    # T├¼m c├íc lead qu├í SLA nh╞░ng ch╞░a bß╗ï gß║»n cß╗¥
    overdue = fetch_all(
        conn,
        """
        SELECT id, full_name, assigned_to, sla_deadline_at, sla_alert_sent
        FROM dbo.leads
        WHERE status = ?
          AND sla_deadline_at IS NOT NULL
          AND sla_deadline_at <= ?
          AND sla_breached = 0
        """,
        (LEAD_STATUS_ASSIGNED, now),
    )

    if not overdue:
        return []

    flagged = []
    cur = conn.cursor()
    for lead in overdue:
        cur.execute(
            "UPDATE dbo.leads SET sla_breached = 1, updated_at = ? WHERE id = ?",
            (now, lead["id"]),
        )
        desc = (
            f"Lead '{lead['full_name']}' (id={lead['id']}) ─æ├ú v╞░ß╗út qu├í SLA phß║ún hß╗ôi 3 ng├áy. "
            f"Ch╞░a ─æ╞░ß╗úc nhß║¡n/tß╗½ chß╗æi. Tr╞░ß╗ƒng nh├│m cß║ºn xem x├⌐t."
        )
        _log_activity(conn, lead["id"], "sla_breached", desc, manager_user_id)
        flagged.append(lead)

    conn.commit()

    # Cß║¡p nhß║¡t cß╗¥ sla_alert_sent ─æß╗â kh├┤ng gß╗¡i lß║íi
    for lead in flagged:
        if not lead.get("sla_alert_sent"):
            cur.execute(
                "UPDATE dbo.leads SET sla_alert_sent = 1, updated_at = ? WHERE id = ?",
                (now, lead["id"]),
            )
    conn.commit()

    return flagged


def get_sla_breached_leads(
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """Lß║Ñy danh s├ích tß║Ñt cß║ú lead ─æ├ú v╞░ß╗út SLA ─æß╗â tr╞░ß╗ƒng nh├│m xem x├⌐t."""
    conn = get_db()
    ensure_leads_tables(conn)
    now = _now_ms()

    where_sql = """
        (l.sla_breached = 1 OR
         (l.sla_deadline_at IS NOT NULL AND l.sla_deadline_at <= ? AND l.status = ?))
    """
    params = [now, LEAD_STATUS_ASSIGNED]

    count_row = fetch_one(
        conn,
        f"SELECT COUNT(*) AS total FROM dbo.leads l WHERE {where_sql}",
        params,
    )
    total = count_row["total"] if count_row else 0

    offset = max(0, (page - 1) * per_page)
    sql = f"""
        SELECT l.id, l.full_name, l.email, l.phone, l.company, l.source,
               l.classification, l.status, l.assigned_to, l.assigned_at,
               l.sla_deadline_at, l.sla_breached, l.rejection_reason,
               l.rejection_count, l.created_at, l.updated_at,
               u_assigned.full_name AS assigned_to_name,
               u_creator.full_name  AS creator_name
        FROM dbo.leads l
        LEFT JOIN dbo.users u_assigned ON l.assigned_to = u_assigned.id
        LEFT JOIN dbo.users u_creator  ON l.created_by  = u_creator.id
        WHERE {where_sql}
        ORDER BY l.sla_deadline_at ASC, l.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    items = fetch_all(conn, sql, params + [offset, max(1, per_page)])
    for item in items:
        item["sla_status"] = "breached"

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def get_lead_activities(lead_id: int) -> list[dict[str, Any]]:
    """Lß║Ñy lß╗ïch sß╗¡ hoß║ít ─æß╗Öng cß╗ºa lead (mß╗¢i nhß║Ñt tr╞░ß╗¢c)."""
    conn = get_db()
    ensure_leads_tables(conn)
    return fetch_all(
        conn,
        """
        SELECT a.id, a.lead_id, a.activity_type, a.description, a.performed_by,
               u.full_name AS performer_name, a.created_at
        FROM dbo.lead_activities a
        LEFT JOIN dbo.users u ON a.performed_by = u.id
        WHERE a.lead_id = ?
        ORDER BY a.id DESC
        """,
        (lead_id,),
    )


def _log_activity(conn, lead_id: int, activity_type: str, description: str, performed_by: int | None) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.lead_activities (lead_id, activity_type, description, performed_by, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (lead_id, activity_type, description, performed_by, _now_ms()),
    )


def update_lead(
    lead_id: int,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company: str | None = None,
    source: str | None = None,
    classification: str | None = None,
    notes: str | None = None,
    updated_by: int | None = None,
) -> dict[str, Any]:
    """Cß║¡p nhß║¡t th├┤ng tin lead (kh├┤ng thay ─æß╗òi trß║íng th├íi luß╗ông)."""
    conn = get_db()
    ensure_leads_tables(conn)
    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")
    if lead["status"] == LEAD_STATUS_CONVERTED:
        raise ValueError("lead_already_converted")

    now = _now_ms()
    sets = []
    params: list[Any] = []

    if full_name is not None:
        full_name = full_name.strip()
        if not full_name:
            raise ValueError("lead_name_empty")
        sets.append("full_name = ?"); params.append(full_name)
    if email is not None:
        sets.append("email = ?"); params.append(email.strip())
    if phone is not None:
        sets.append("phone = ?"); params.append(phone.strip())
    if company is not None:
        sets.append("company = ?"); params.append(company.strip())
    if source is not None:
        sets.append("source = ?"); params.append(source.strip())
    if classification is not None:
        cl = classification.strip().lower()
        if cl in {"hot", "warm", "cold"}:
            sets.append("classification = ?"); params.append(cl)
    if notes is not None:
        sets.append("notes = ?"); params.append(notes.strip())

    if not sets:
        return lead  # Kh├┤ng c├│ g├¼ thay ─æß╗òi

    sets.append("updated_at = ?"); params.append(now)
    params.append(lead_id)

    cur = conn.cursor()
    cur.execute(f"UPDATE dbo.leads SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()

    _log_activity(conn, lead_id, "updated", "Th├┤ng tin lead ─æ╞░ß╗úc cß║¡p nhß║¡t.", updated_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def delete_lead(lead_id: int) -> bool:
    """X├│a lead v├á to├án bß╗Ö lß╗ïch sß╗¡ hoß║ít ─æß╗Öng li├¬n quan."""
    conn = get_db()
    ensure_leads_tables(conn)
    lead = _get_lead_raw(conn, lead_id)
    if not lead:
        raise LookupError("lead_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.lead_activities WHERE lead_id = ?", (lead_id,))
    cur.execute("DELETE FROM dbo.leads WHERE id = ?", (lead_id,))
    conn.commit()
    return True
