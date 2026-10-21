"""
app/tasks_reminders.py ΓÇö Quß║ún l├╜ C├┤ng viß╗çc, Nhß║»c viß╗çc sß║»p ─æß║┐n hß║ín & Xß╗¡ l├╜ Qu├í hß║ín (SCRUM-103)

Mß╗Ñc ti├¬u:
- Quß║ún l├╜ c├┤ng viß╗çc (tasks) li├¬n kß║┐t kh├ích h├áng, c╞í hß╗Öi kinh doanh v├á ng╞░ß╗¥i thß╗▒c hiß╗çn
- X├íc ─æß╗ïnh c├┤ng viß╗çc sß║»p ─æß║┐n hß║ín theo c├íc mß╗æc cß║Ñu h├¼nh (24h, 1h...)
- X├íc ─æß╗ïnh c├┤ng viß╗çc qu├í hß║ín (due_date < now v├á ch╞░a ho├án th├ánh/hß╗ºy)
- Tß╗▒ ─æß╗Öng tß║ío th├┤ng b├ío (notifications) trong ß╗⌐ng dß╗Ñng, ng─ân chß║╖n tß║ío th├┤ng b├ío tr├╣ng lß║╖p
- Cung cß║Ñp API thß╗æng k├¬ c├┤ng viß╗çc qu├í hß║ín theo th├ánh vi├¬n nh├│m cho Tr╞░ß╗ƒng nh├│m/Admin
- Bß╗Ö xß╗¡ l├╜ nß╗ün (Scheduler) ─æß╗ïnh kß╗│ kiß╗âm tra thß╗¥i hß║ín, an to├án khi reload Flask
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

from app.db import fetch_all, fetch_one, get_db

logger = logging.getLogger(__name__)

# Trß║íng th├íi c├┤ng viß╗çc
TASK_STATUS_PENDING = "pending"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_CANCELLED = "cancelled"
ACTIVE_TASK_STATUSES = {TASK_STATUS_PENDING, TASK_STATUS_IN_PROGRESS}

# Loß║íi th├┤ng b├ío
NOTIF_TYPE_DUE_SOON = "task_due_soon"
NOTIF_TYPE_OVERDUE = "task_overdue"
NOTIF_TYPE_GENERAL = "general"

# Mß╗æc nhß║»c viß╗çc mß║╖c ─æß╗ïnh
DEFAULT_MILESTONES = ["24h", "1h"]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    name = getattr(type(conn), "__name__", "").lower()
    return "sqlite" in mod or "sqlite" in name


def ensure_tasks_tables(conn) -> None:
    """Tß╗▒ ─æß╗Öng khß╗ƒi tß║ío c├íc bß║úng dbo.tasks, dbo.notifications, dbo.task_reminder_settings nß║┐u ch╞░a c├│."""
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT NULL,
                assigned_to     INTEGER NOT NULL,
                created_by      INTEGER NOT NULL,
                customer_id     INTEGER NULL,
                opportunity_id  INTEGER NULL,
                due_date        INTEGER NOT NULL,
                priority        TEXT NOT NULL DEFAULT 'medium',
                status          TEXT NOT NULL DEFAULT 'pending',
                completed_at    INTEGER NULL,
                created_at      INTEGER NOT NULL,
                updated_at      INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL,
                title               TEXT NOT NULL,
                message             TEXT NOT NULL,
                type                TEXT NOT NULL DEFAULT 'task_reminder',
                reference_type      TEXT NULL,
                reference_id        INTEGER NULL,
                reminder_milestone  TEXT NULL,
                is_read             INTEGER NOT NULL DEFAULT 0,
                read_at             INTEGER NULL,
                created_at          INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS UX_notif_dedup
            ON notifications (user_id, reference_type, reference_id, reminder_milestone);
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task_reminder_settings (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id                 INTEGER NOT NULL UNIQUE,
                milestones_json         TEXT NOT NULL DEFAULT '["24h", "1h"]',
                is_email_notification   INTEGER NOT NULL DEFAULT 0,
                created_at              INTEGER NOT NULL,
                updated_at              INTEGER NOT NULL
            );
            """
        )
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tasks' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.tasks (
                id               INT            IDENTITY(1,1) NOT NULL PRIMARY KEY,
                title            NVARCHAR(250)  NOT NULL,
                description      NVARCHAR(MAX)  NULL,
                assigned_to      INT            NOT NULL,
                created_by       INT            NOT NULL,
                customer_id      INT            NULL,
                opportunity_id   INT            NULL,
                due_date         BIGINT         NOT NULL,
                priority         NVARCHAR(50)   NOT NULL CONSTRAINT DF_tasks_priority DEFAULT (N'medium'),
                status           NVARCHAR(50)   NOT NULL CONSTRAINT DF_tasks_status DEFAULT (N'pending'),
                completed_at     BIGINT         NULL,
                created_at       BIGINT         NOT NULL,
                updated_at       BIGINT         NOT NULL,
                CONSTRAINT FK_tasks_assigned_to FOREIGN KEY (assigned_to) REFERENCES dbo.users(id),
                CONSTRAINT FK_tasks_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id)
            );
            CREATE INDEX IX_tasks_assigned_to_due_date ON dbo.tasks (assigned_to, status, due_date ASC);
            CREATE INDEX IX_tasks_status_due_date ON dbo.tasks (status, due_date ASC);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'notifications' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.notifications (
                id                  BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
                user_id             INT            NOT NULL,
                title               NVARCHAR(250)  NOT NULL,
                message             NVARCHAR(MAX)  NOT NULL,
                type                NVARCHAR(50)   NOT NULL CONSTRAINT DF_notif_type DEFAULT (N'task_reminder'),
                reference_type      NVARCHAR(50)   NULL,
                reference_id        INT            NULL,
                reminder_milestone  NVARCHAR(50)   NULL,
                is_read             BIT            NOT NULL CONSTRAINT DF_notif_is_read DEFAULT (0),
                read_at             BIGINT         NULL,
                created_at          BIGINT         NOT NULL,
                CONSTRAINT FK_notif_user FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
            );
            CREATE INDEX IX_notif_user_read_created ON dbo.notifications (user_id, is_read, created_at DESC);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'task_reminder_settings' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.task_reminder_settings (
                id                      INT           IDENTITY(1,1) NOT NULL PRIMARY KEY,
                user_id                 INT           NOT NULL UNIQUE,
                milestones_json         NVARCHAR(255) NOT NULL CONSTRAINT DF_trs_milestones DEFAULT (N'["24h", "1h"]'),
                is_email_notification   BIT           NOT NULL CONSTRAINT DF_trs_email DEFAULT (0),
                created_at              BIGINT        NOT NULL,
                updated_at              BIGINT        NOT NULL,
                CONSTRAINT FK_trs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
            );
        END
        """
    )
    conn.commit()


def parse_milestone_ms(milestone_str: str) -> int:
    """Chuyß╗ân ─æß╗òi chuß╗ùi mß╗æc nhß║»c viß╗çc (vd '24h', '1h', '30m') th├ánh milliseconds."""
    s = milestone_str.strip().lower()
    if s.endswith("h"):
        hours = float(s[:-1])
        return int(hours * 3600 * 1000)
    elif s.endswith("m"):
        mins = float(s[:-1])
        return int(mins * 60 * 1000)
    elif s.endswith("d"):
        days = float(s[:-1])
        return int(days * 86400 * 1000)
    try:
        val = float(s)
        return int(val * 3600 * 1000)  # Mß║╖c ─æß╗ïnh coi l├á sß╗æ giß╗¥
    except ValueError:
        return 24 * 3600 * 1000


# ΓöÇΓöÇΓöÇ Task CRUD ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_task(
    title: str,
    due_date: int,
    assigned_to: int,
    created_by: int,
    description: str = "",
    customer_id: int | None = None,
    opportunity_id: int | None = None,
    priority: str = "medium",
    status: str = "pending",
    conn: Any = None,
) -> dict[str, Any]:
    """Tß║ío mß╗¢i mß╗Öt c├┤ng viß╗çc."""
    if not title or not title.strip():
        raise ValueError("Ti├¬u ─æß╗ü c├┤ng viß╗çc kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng.")
    if not due_date or due_date <= 0:
        raise ValueError("Thß╗¥i hß║ín ho├án th├ánh kh├┤ng hß╗úp lß╗ç.")

    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    # Kiß╗âm tra ng╞░ß╗¥i ─æ╞░ß╗úc giao
    user_row = fetch_one(conn, "SELECT id, is_active FROM dbo.users WHERE id = ?", (assigned_to,))
    if not user_row:
        raise ValueError("Ng╞░ß╗¥i ─æ╞░ß╗úc giao c├┤ng viß╗çc kh├┤ng tß╗ôn tß║íi.")
    if not user_row.get("is_active", True):
        raise ValueError("Ng╞░ß╗¥i ─æ╞░ß╗úc giao c├┤ng viß╗çc ─æ├ú bß╗ï v├┤ hiß╗çu h├│a.")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.tasks
            (title, description, assigned_to, created_by, customer_id, opportunity_id,
             due_date, priority, status, completed_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
        """,
        (
            title.strip(),
            description.strip() if description else None,
            assigned_to,
            created_by,
            customer_id,
            opportunity_id,
            due_date,
            priority or "medium",
            status or "pending",
            now,
            now,
        ),
    )
    if _is_sqlite(conn):
        task_id = cur.lastrowid
    else:
        id_row = fetch_one(conn, "SELECT @@IDENTITY AS id")
        task_id = int(id_row["id"]) if id_row and id_row.get("id") else 0
    conn.commit()

    return get_task_by_id(task_id, conn=conn)  # type: ignore


def get_task_by_id(task_id: int, conn: Any = None) -> dict[str, Any] | None:
    """Lß║Ñy chi tiß║┐t c├┤ng viß╗çc theo ID."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    row = fetch_one(
        conn,
        """
        SELECT t.id, t.title, t.description, t.assigned_to, u.full_name AS assignee_name,
               t.created_by, c.name AS customer_name, t.customer_id,
               o.title AS opportunity_title, t.opportunity_id,
               t.due_date, t.priority, t.status, t.completed_at,
               t.created_at, t.updated_at
        FROM dbo.tasks t
        LEFT JOIN dbo.users u ON t.assigned_to = u.id
        LEFT JOIN dbo.customers c ON t.customer_id = c.id
        LEFT JOIN dbo.opportunities o ON t.opportunity_id = o.id
        WHERE t.id = ?
        """,
        (task_id,),
    )
    if not row:
        return None

    now = _now_ms()
    due = int(row["due_date"])
    is_overdue = due < now and row["status"] in ACTIVE_TASK_STATUSES
    overdue_hours = round((now - due) / (3600 * 1000), 1) if is_overdue else 0

    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "description": row.get("description") or "",
        "assigned_to": int(row["assigned_to"]),
        "assignee_name": str(row.get("assignee_name") or ""),
        "created_by": int(row["created_by"]),
        "customer_id": row["customer_id"],
        "customer_name": row.get("customer_name") or "",
        "opportunity_id": row["opportunity_id"],
        "opportunity_title": row.get("opportunity_title") or "",
        "due_date": due,
        "priority": str(row["priority"]),
        "status": str(row["status"]),
        "is_overdue": is_overdue,
        "overdue_hours": overdue_hours,
        "completed_at": row.get("completed_at"),
        "created_at": int(row["created_at"]),
        "updated_at": int(row["updated_at"]),
    }


def update_task_status(task_id: int, status: str, conn: Any = None) -> dict[str, Any] | None:
    """Cß║¡p nhß║¡t trß║íng th├íi c├┤ng viß╗çc."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    now = _now_ms()
    completed_at = now if status == TASK_STATUS_COMPLETED else None
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.tasks
        SET status = ?, completed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, completed_at, now, task_id),
    )
    conn.commit()
    return get_task_by_id(task_id, conn=conn)


# ΓöÇΓöÇΓöÇ Cß║Ñu h├¼nh Mß╗æc Nhß║»c viß╗çc (Task Reminder Settings) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def get_user_reminder_settings(user_id: int, conn: Any = None) -> list[str]:
    """Lß║Ñy danh s├ích c├íc mß╗æc nhß║»c tr╞░ß╗¢c hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng (mß║╖c ─æß╗ïnh ['24h', '1h'])."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    row = fetch_one(conn, "SELECT milestones_json FROM dbo.task_reminder_settings WHERE user_id = ?", (user_id,))
    if not row or not row.get("milestones_json"):
        return list(DEFAULT_MILESTONES)
    try:
        val = json.loads(str(row["milestones_json"]))
        return val if isinstance(val, list) and val else list(DEFAULT_MILESTONES)
    except Exception:
        return list(DEFAULT_MILESTONES)


def update_user_reminder_settings(user_id: int, milestones: list[str], conn: Any = None) -> list[str]:
    """Cß║¡p nhß║¡t cß║Ñu h├¼nh c├íc mß╗æc nhß║»c viß╗çc cho ng╞░ß╗¥i d├╣ng."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    clean_milestones = [str(m).strip() for m in milestones if str(m).strip()]
    if not clean_milestones:
        clean_milestones = list(DEFAULT_MILESTONES)

    milestones_str = json.dumps(clean_milestones)
    now = _now_ms()
    cur = conn.cursor()

    existing = fetch_one(conn, "SELECT id FROM dbo.task_reminder_settings WHERE user_id = ?", (user_id,))
    if existing:
        cur.execute(
            "UPDATE dbo.task_reminder_settings SET milestones_json = ?, updated_at = ? WHERE user_id = ?",
            (milestones_str, now, user_id),
        )
    else:
        cur.execute(
            """
            INSERT INTO dbo.task_reminder_settings (user_id, milestones_json, is_email_notification, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?)
            """,
            (user_id, milestones_str, now, now),
        )
    conn.commit()
    return clean_milestones


# ΓöÇΓöÇΓöÇ X├íc ─æß╗ïnh C├┤ng viß╗çc Sß║»p ─æß║┐n hß║ín & Qu├í hß║ín ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def list_user_due_soon_tasks(user_id: int, conn: Any = None) -> list[dict[str, Any]]:
    """
    Lß║Ñy danh s├ích c├┤ng viß╗çc sß║»p ─æß║┐n hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi
    (trong khoß║úng thß╗¥i gian tß╗½ hiß╗çn tß║íi tß╗¢i mß╗æc nhß║»c xa nhß║Ñt ─æ╞░ß╗úc cß║Ñu h├¼nh).
    """
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    milestones = get_user_reminder_settings(user_id, conn=conn)
    max_ms = max([parse_milestone_ms(m) for m in milestones] or [24 * 3600 * 1000])

    now = _now_ms()
    max_due = now + max_ms

    rows = fetch_all(
        conn,
        """
        SELECT t.id, t.title, t.description, t.assigned_to, t.customer_id, c.name AS customer_name,
               t.opportunity_id, o.title AS opportunity_title, t.due_date, t.priority, t.status
        FROM dbo.tasks t
        LEFT JOIN dbo.customers c ON t.customer_id = c.id
        LEFT JOIN dbo.opportunities o ON t.opportunity_id = o.id
        WHERE t.assigned_to = ?
          AND t.status IN ('pending', 'in_progress')
          AND t.due_date >= ?
          AND t.due_date <= ?
        ORDER BY t.due_date ASC
        """,
        (user_id, now, max_due),
    )

    result = []
    for r in rows:
        due = int(r["due_date"])
        hours_left = max(0.0, round((due - now) / (3600 * 1000), 1))
        result.append(
            {
                "id": int(r["id"]),
                "title": str(r["title"]),
                "description": r.get("description") or "",
                "due_date": due,
                "hours_left": hours_left,
                "priority": str(r["priority"]),
                "status": str(r["status"]),
                "customer_name": r.get("customer_name") or "",
                "opportunity_title": r.get("opportunity_title") or "",
            }
        )
    return result


def list_user_overdue_tasks(user_id: int, conn: Any = None) -> list[dict[str, Any]]:
    """
    Lß║Ñy danh s├ích c├┤ng viß╗çc qu├í hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi
    (due_date < now v├á ch╞░a ho├án th├ánh/hß╗ºy).
    """
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    now = _now_ms()
    rows = fetch_all(
        conn,
        """
        SELECT t.id, t.title, t.description, t.assigned_to, t.customer_id, c.name AS customer_name,
               t.opportunity_id, o.title AS opportunity_title, t.due_date, t.priority, t.status
        FROM dbo.tasks t
        LEFT JOIN dbo.customers c ON t.customer_id = c.id
        LEFT JOIN dbo.opportunities o ON t.opportunity_id = o.id
        WHERE t.assigned_to = ?
          AND t.status IN ('pending', 'in_progress')
          AND t.due_date < ?
        ORDER BY t.due_date ASC
        """,
        (user_id, now),
    )

    result = []
    for r in rows:
        due = int(r["due_date"])
        overdue_hours = max(0.1, round((now - due) / (3600 * 1000), 1))
        result.append(
            {
                "id": int(r["id"]),
                "title": str(r["title"]),
                "description": r.get("description") or "",
                "due_date": due,
                "overdue_hours": overdue_hours,
                "priority": str(r["priority"]),
                "status": str(r["status"]),
                "customer_name": r.get("customer_name") or "",
                "opportunity_title": r.get("opportunity_title") or "",
            }
        )
    return result


# ΓöÇΓöÇΓöÇ Quß║ún l├╜ Th├┤ng b├ío (Notifications) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_notification_if_not_exists(
    user_id: int,
    title: str,
    message: str,
    notif_type: str,
    reference_type: str = "task",
    reference_id: int | None = None,
    reminder_milestone: str | None = None,
    conn: Any = None,
) -> bool:
    """Tß║ío th├┤ng b├ío nß║┐u ch╞░a tß╗½ng tß╗ôn tß║íi th├┤ng b├ío t╞░╞íng ß╗⌐ng (chß╗æng tr├╣ng lß║╖p)."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    # Kiß╗âm tra tr├╣ng lß║╖p
    existing = fetch_one(
        conn,
        """
        SELECT id FROM dbo.notifications
        WHERE user_id = ? AND reference_type = ? AND reference_id = ? AND reminder_milestone = ?
        """,
        (user_id, reference_type, reference_id, reminder_milestone),
    )
    if existing:
        return False

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.notifications
            (user_id, title, message, type, reference_type, reference_id, reminder_milestone, is_read, read_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
        """,
        (user_id, title, message, notif_type, reference_type, reference_id, reminder_milestone, now),
    )
    conn.commit()
    return True


def list_user_notifications(
    user_id: int,
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
    conn: Any = None,
) -> dict[str, Any]:
    """Lß║Ñy danh s├ích th├┤ng b├ío cß╗ºa ng╞░ß╗¥i d├╣ng vß╗¢i ph├ón trang v├á bß╗Ö lß╗ìc ch╞░a ─æß╗ìc."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    where_clauses = ["user_id = ?"]
    params: list[Any] = [user_id]

    if unread_only:
        where_clauses.append("is_read = 0")

    where_sql = " AND ".join(where_clauses)
    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.notifications WHERE {where_sql}", params)
    total = int(count_row["total"]) if count_row else 0

    unread_row = fetch_one(conn, "SELECT COUNT(*) AS unread FROM dbo.notifications WHERE user_id = ? AND is_read = 0", (user_id,))
    unread_count = int(unread_row["unread"]) if unread_row else 0

    offset = (page - 1) * per_page
    rows = fetch_all(
        conn,
        f"""
        SELECT id, user_id, title, message, type, reference_type, reference_id,
               reminder_milestone, is_read, read_at, created_at
        FROM dbo.notifications
        WHERE {where_sql}
        ORDER BY created_at DESC
        """,
        params,
    )

    # Ph├ón trang tß║íi tß║ºng Python nß║┐u d├╣ng mock / sqlite, hoß║╖c slice
    paged_rows = rows[offset : offset + per_page]

    items = []
    for r in paged_rows:
        items.append(
            {
                "id": int(r["id"]),
                "user_id": int(r["user_id"]),
                "title": str(r["title"]),
                "message": str(r["message"]),
                "type": str(r["type"]),
                "reference_type": r.get("reference_type"),
                "reference_id": r.get("reference_id"),
                "reminder_milestone": r.get("reminder_milestone"),
                "is_read": bool(r["is_read"]),
                "read_at": r.get("read_at"),
                "created_at": int(r["created_at"]),
            }
        )

    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


def mark_notification_as_read(notification_id: int, user_id: int, conn: Any = None) -> bool:
    """─É├ính dß║Ñu mß╗Öt th├┤ng b├ío ─æ├ú ─æß╗ìc."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    notif = fetch_one(conn, "SELECT id FROM dbo.notifications WHERE id = ? AND user_id = ?", (notification_id, user_id))
    if not notif:
        return False

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.notifications SET is_read = 1, read_at = ? WHERE id = ?",
        (now, notification_id),
    )
    conn.commit()
    return True


def mark_all_notifications_as_read(user_id: int, conn: Any = None) -> int:
    """─É├ính dß║Ñu tß║Ñt cß║ú th├┤ng b├ío cß╗ºa ng╞░ß╗¥i d├╣ng ─æ├ú ─æß╗ìc."""
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        "UPDATE dbo.notifications SET is_read = 1, read_at = ? WHERE user_id = ? AND is_read = 0",
        (now, user_id),
    )
    affected = cur.rowcount if hasattr(cur, "rowcount") and cur.rowcount is not None else 1
    conn.commit()
    return max(0, affected)


# ΓöÇΓöÇΓöÇ Bß╗Ö xß╗¡ l├╜ ─Éß╗ïnh kß╗│ Kiß╗âm tra Hß║ín c├┤ng viß╗çc (Periodic Check Engine) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def process_task_reminders_and_overdue(conn: Any = None) -> dict[str, int]:
    """
    Qu├⌐t to├án bß╗Ö c├┤ng viß╗çc ─æang hoß║ít ─æß╗Öng v├á tß║ío th├┤ng b├ío:
    - C├┤ng viß╗çc qu├í hß║ín: tß║ío th├┤ng b├ío mß╗æc 'overdue' (chß╗ë 1 lß║ºn duy nhß║Ñt).
    - C├┤ng viß╗çc sß║»p ─æß║┐n hß║ín: kiß╗âm tra tß╗½ng mß╗æc cß║Ñu h├¼nh (24h, 1h...) v├á tß║ío th├┤ng b├ío (chß╗ë 1 lß║ºn duy nhß║Ñt cho mß╗ùi mß╗æc).
    """
    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    now = _now_ms()
    active_tasks = fetch_all(
        conn,
        """
        SELECT id, title, assigned_to, due_date, status
        FROM dbo.tasks
        WHERE status IN ('pending', 'in_progress')
        """,
    )

    created_overdue_count = 0
    created_due_soon_count = 0

    for t in active_tasks:
        task_id = int(t["id"])
        user_id = int(t["assigned_to"])
        due_date = int(t["due_date"])
        title = str(t["title"])

        # Format ng├áy giß╗¥ dß╗à ─æß╗ìc
        dt_str = datetime.fromtimestamp(due_date / 1000.0, tz=timezone.utc).strftime("%d/%m/%Y %H:%M")

        # 1. Qu├í hß║ín
        if due_date < now:
            created = create_notification_if_not_exists(
                user_id=user_id,
                title=f"ΓÜá∩╕Å C├┤ng viß╗çc qu├í hß║ín: {title}",
                message=f"C├┤ng viß╗çc '{title}' ─æ├ú qu├í hß║ín v├áo l├║c {dt_str} UTC. Vui l├▓ng kiß╗âm tra v├á xß╗¡ l├╜ ngay.",
                notif_type=NOTIF_TYPE_OVERDUE,
                reference_type="task",
                reference_id=task_id,
                reminder_milestone="overdue",
                conn=conn,
            )
            if created:
                created_overdue_count += 1
        else:
            # 2. Sß║»p ─æß║┐n hß║ín: kiß╗âm tra c├íc mß╗æc cß╗ºa ng╞░ß╗¥i d├╣ng
            milestones = get_user_reminder_settings(user_id, conn=conn)
            for m in milestones:
                m_ms = parse_milestone_ms(m)
                # Nß║┐u thß╗¥i ─æiß╗âm hiß╗çn tß║íi nß║▒m trong cß╗¡a sß╗ò nhß║»c viß╗çc [due - m_ms, due]
                if now >= (due_date - m_ms):
                    created = create_notification_if_not_exists(
                        user_id=user_id,
                        title=f"ΓÅ░ Nhß║»c viß╗çc sß║»p ─æß║┐n hß║ín ({m}): {title}",
                        message=f"C├┤ng viß╗çc '{title}' sß║»p ─æß║┐n hß║ín v├áo l├║c {dt_str} UTC (c├▓n d╞░ß╗¢i {m}).",
                        notif_type=NOTIF_TYPE_DUE_SOON,
                        reference_type="task",
                        reference_id=task_id,
                        reminder_milestone=m,
                        conn=conn,
                    )
                    if created:
                        created_due_soon_count += 1

    return {
        "overdue_notifications_created": created_overdue_count,
        "due_soon_notifications_created": created_due_soon_count,
    }


# ΓöÇΓöÇΓöÇ Thß╗æng k├¬ d├ánh cho Tr╞░ß╗ƒng nh├│m (Leader/Manager Overdue Summary) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def get_team_overdue_summary(current_user: Any, conn: Any = None) -> list[dict[str, Any]]:
    """
    Thß╗æng k├¬ tß╗òng sß╗æ c├┤ng viß╗çc qu├í hß║ín cß╗ºa tß╗½ng th├ánh vi├¬n trong phß║ím vi quß║ún l├╜:
    - Quß║ún trß╗ï vi├¬n (admin): xem to├án bß╗Ö hß╗ç thß╗æng.
    - Tr╞░ß╗ƒng nh├│m (manager): xem c├íc th├ánh vi├¬n thuß╗Öc nh├│m m├¼nh quß║ún l├╜ (c├╣ng group_name hoß║╖c nh├│m ─æ╞░ß╗úc cß║Ñp quyß╗ün).
    - Nh├ón vi├¬n th├┤ng th╞░ß╗¥ng (employee): kh├┤ng ─æ╞░ß╗úc ph├⌐p truy cß║¡p (trß║ú vß╗ü lß╗ùi PermissionError).
    """
    if current_user.role not in {"admin", "manager"}:
        raise PermissionError("Bß║ín kh├┤ng c├│ quyß╗ün xem thß╗æng k├¬ c├┤ng viß╗çc qu├í hß║ín cß╗ºa nh├│m.")

    if conn is None:
        conn = get_db()
    ensure_tasks_tables(conn)

    now = _now_ms()

    # X├íc ─æß╗ïnh danh s├ích th├ánh vi├¬n thuß╗Öc phß║ím vi
    if current_user.role == "admin":
        members = fetch_all(conn, "SELECT id, full_name, email, role, group_name FROM dbo.users WHERE is_active = 1")
    else:
        # Lß║Ñy nh├│m cß╗ºa manager hiß╗çn tß║íi
        mgr_row = fetch_one(conn, "SELECT group_name FROM dbo.users WHERE id = ?", (current_user.id,))
        mgr_group = mgr_row.get("group_name") if mgr_row else ""
        if mgr_group:
            members = fetch_all(
                conn,
                "SELECT id, full_name, email, role, group_name FROM dbo.users WHERE is_active = 1 AND (group_name = ? OR id = ?)",
                (mgr_group, current_user.id),
            )
        else:
            members = fetch_all(
                conn,
                "SELECT id, full_name, email, role, group_name FROM dbo.users WHERE is_active = 1",
            )

    summary_list = []
    for m in members:
        uid = int(m["id"])
        overdue_tasks = fetch_all(
            conn,
            """
            SELECT t.id, t.title, t.due_date, t.priority, t.status,
                   c.name AS customer_name, o.title AS opportunity_title
            FROM dbo.tasks t
            LEFT JOIN dbo.customers c ON t.customer_id = c.id
            LEFT JOIN dbo.opportunities o ON t.opportunity_id = o.id
            WHERE t.assigned_to = ?
              AND t.status IN ('pending', 'in_progress')
              AND t.due_date < ?
            ORDER BY t.due_date ASC
            """,
            (uid, now),
        )

        tasks_data = []
        for t in overdue_tasks:
            due = int(t["due_date"])
            tasks_data.append(
                {
                    "id": int(t["id"]),
                    "title": str(t["title"]),
                    "due_date": due,
                    "overdue_hours": max(0.1, round((now - due) / (3600 * 1000), 1)),
                    "priority": str(t["priority"]),
                    "status": str(t["status"]),
                    "customer_name": t.get("customer_name") or "",
                    "opportunity_title": t.get("opportunity_title") or "",
                }
            )

        summary_list.append(
            {
                "user_id": uid,
                "full_name": str(m["full_name"]),
                "email": str(m["email"]),
                "role": str(m["role"]),
                "group_name": str(m.get("group_name") or ""),
                "overdue_count": len(tasks_data),
                "overdue_tasks": tasks_data,
            }
        )

    # Sß║»p xß║┐p ng╞░ß╗¥i c├│ sß╗æ l╞░ß╗úng qu├í hß║ín nhiß╗üu nhß║Ñt l├¬n ─æß║ºu
    summary_list.sort(key=lambda x: x["overdue_count"], reverse=True)
    return summary_list


# ΓöÇΓöÇΓöÇ Background Scheduler ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

_scheduler_started = False
_scheduler_lock = threading.Lock()


def start_reminder_scheduler(app=None) -> None:
    """Khß╗ƒi tß║ío background thread chß║íy ─æß╗ïnh kß╗│ kiß╗âm tra nhß║»c viß╗çc."""
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return

        # Tr├ính nh├ón ─æ├┤i thread khi chß║íy Flask reload debug mode
        if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
            return

        interval = int(os.environ.get("REMINDER_CHECK_INTERVAL_SECONDS", "300"))

        def run_worker():
            logger.info("Task reminder worker started with interval %ds", interval)
            while True:
                try:
                    if app:
                        with app.app_context():
                            process_task_reminders_and_overdue()
                    else:
                        process_task_reminders_and_overdue()
                except Exception as e:
                    logger.error("Error in reminder worker: %s", e)
                time.sleep(interval)

        t = threading.Thread(target=run_worker, daemon=True, name="CRM-TaskReminderWorker")
        t.start()
        _scheduler_started = True
