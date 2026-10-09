"""
app/leads.py — Quản lý Lead: Nhận/Từ chối Lead với ràng buộc SLA phản hồi (SCRUM-84)

Nhân viên kinh doanh có thể:
  1. Nhận lead được phân → lead chuyển sang "Đang chăm sóc"
  2. Từ chối lead (bắt buộc nhập lý do) → lead quay về hàng chờ phân bổ
  3. Quá SLA mà chưa liên hệ → lead gắn cờ sla_breached=True và báo trưởng nhóm
"""
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db

# Trạng thái lead
LEAD_STATUS_NEW = "Mới"                  # Mới tạo, chờ phân bổ
LEAD_STATUS_ASSIGNED = "Đã phân công"   # Đã phân công, nhân viên chưa xác nhận
LEAD_STATUS_CARING = "Đang chăm sóc"   # Nhân viên đã nhận
LEAD_STATUS_WAITING = "Chờ phân bổ"    # Từ chối → quay về hàng chờ
LEAD_STATUS_CONVERTED = "Đã chuyển đổi"  # Đã thành khách hàng
LEAD_STATUS_REJECTED = "Đã từ chối"     # Cuối cùng bị từ chối

# SLA mặc định: 3 ngày (72 giờ) tính bằng milliseconds
SLA_RESPONSE_MS = 3 * 24 * 3600 * 1000


def _now_ms() -> int:
    return int(time.time() * 1000)


def ensure_leads_tables(conn) -> None:
    """Tạo bảng dbo.leads và bảng dbo.lead_activities nếu chưa tồn tại"""
    cur = conn.cursor()

    # Bảng leads chính
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
                -- 'hot' = Nóng | 'warm' = Ấm | 'cold' = Lạnh
                status              NVARCHAR(50)    NOT NULL DEFAULT N'Mới',
                -- Mới | Đã phân công | Đang chăm sóc | Chờ phân bổ | Đã chuyển đổi | Đã từ chối
                assigned_to         INT             NULL,
                -- FK → dbo.users.id (nhân viên được phân công)
                assigned_at         BIGINT          NULL,
                -- Unix ms khi phân công, dùng tính SLA
                sla_deadline_at     BIGINT          NULL,
                -- Hạn chót SLA = assigned_at + 3 ngày
                sla_breached        BIT             NOT NULL DEFAULT 0,
                -- 1 nếu đã vượt SLA mà chưa nhận/từ chối
                sla_alert_sent      BIT             NOT NULL DEFAULT 0,
                -- 1 nếu đã gửi cảnh báo SLA cho trưởng nhóm
                rejection_reason    NVARCHAR(1000)  NULL,
                -- Lý do từ chối (bắt buộc khi từ chối)
                rejection_count     INT             NOT NULL DEFAULT 0,
                -- Số lần đã bị từ chối
                converted_at        BIGINT          NULL,
                -- Khi nào chuyển đổi thành khách hàng
                customer_id         INT             NULL,
                -- FK → dbo.customers.id (sau khi chuyển đổi)
                notes               NVARCHAR(MAX)   NULL,
                created_by          INT             NOT NULL,
                created_at          BIGINT          NOT NULL,
                updated_at          BIGINT          NOT NULL
            );
        END
        """
    )
    conn.commit()

    # Bảng lịch sử hoạt động của lead
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
                -- FK → dbo.users.id
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
    # Tính trạng thái SLA theo thời gian thực
    row["sla_status"] = _compute_sla_status(row)
    return row


def _compute_sla_status(lead: dict) -> str:
    """Trả về: 'ok' | 'warning' | 'breached' | 'not_assigned'"""
    if not lead.get("assigned_at"):
        return "not_assigned"
    now = _now_ms()
    deadline = lead.get("sla_deadline_at") or 0
    if lead.get("sla_breached"):
        return "breached"
    if deadline > 0 and now >= deadline:
        return "breached"
    # Cảnh báo khi còn dưới 8 giờ
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
    Danh sách lead với các bộ lọc. (dùng chung cho SCRUM-84 & SCRUM-86)
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
    """Tạo lead mới, trạng thái ban đầu là 'Mới'."""
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

    _log_activity(conn, lead_id, "created", f"Lead '{full_name}' được tạo mới.", created_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def assign_lead(lead_id: int, assigned_to: int, assigned_by: int) -> dict[str, Any]:
    """
    Phân công lead cho nhân viên kinh doanh.
    - Đặt trạng thái → 'Đã phân công'
    - Ghi nhận thời điểm phân công và tính SLA deadline (assigned_at + 3 ngày)
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
                  f"Lead được phân công cho '{name}'. SLA hạn chót: {sla_deadline} ms.",
                  assigned_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def accept_lead(lead_id: int, user_id: int) -> dict[str, Any]:
    """
    Nhân viên nhận lead → lead chuyển sang 'Đang chăm sóc'.
    Chỉ nhân viên được phân công mới có thể nhận.
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
                  f"Nhân viên (id={user_id}) đã nhận lead và bắt đầu chăm sóc.",
                  user_id)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def reject_lead(lead_id: int, user_id: int, reason: str) -> dict[str, Any]:
    """
    Nhân viên từ chối lead (bắt buộc phải có lý do).
    Lead quay về trạng thái 'Chờ phân bổ' và tăng rejection_count.
    Chỉ nhân viên được phân công mới có thể từ chối.
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
                  f"Nhân viên (id={user_id}) từ chối lead. Lý do: {reason}",
                  user_id)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def check_and_flag_sla_breached_leads(manager_user_id: int | None = None) -> list[dict[str, Any]]:
    """
    Quét tất cả lead đã phân công nhưng quá SLA deadline mà chưa được nhận/từ chối.
    → Gắn cờ sla_breached = 1
    → Ghi activity cảnh báo cho trưởng nhóm

    Hàm này nên được gọi định kỳ (scheduler / cronjob) hoặc khi nhân viên mở danh sách lead.
    Trả về danh sách lead vừa bị gắn cờ SLA vi phạm.
    """
    conn = get_db()
    ensure_leads_tables(conn)
    now = _now_ms()

    # Tìm các lead quá SLA nhưng chưa bị gắn cờ
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
            f"Lead '{lead['full_name']}' (id={lead['id']}) đã vượt quá SLA phản hồi 3 ngày. "
            f"Chưa được nhận/từ chối. Trưởng nhóm cần xem xét."
        )
        _log_activity(conn, lead["id"], "sla_breached", desc, manager_user_id)
        flagged.append(lead)

    conn.commit()

    # Cập nhật cờ sla_alert_sent để không gửi lại
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
    """Lấy danh sách tất cả lead đã vượt SLA để trưởng nhóm xem xét."""
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
    """Lấy lịch sử hoạt động của lead (mới nhất trước)."""
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
    """Cập nhật thông tin lead (không thay đổi trạng thái luồng)."""
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
        return lead  # Không có gì thay đổi

    sets.append("updated_at = ?"); params.append(now)
    params.append(lead_id)

    cur = conn.cursor()
    cur.execute(f"UPDATE dbo.leads SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()

    _log_activity(conn, lead_id, "updated", "Thông tin lead được cập nhật.", updated_by)
    conn.commit()

    return get_lead(lead_id)  # type: ignore


def delete_lead(lead_id: int) -> bool:
    """Xóa lead và toàn bộ lịch sử hoạt động liên quan."""
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
