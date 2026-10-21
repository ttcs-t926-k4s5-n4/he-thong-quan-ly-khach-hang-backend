"""
app/call_logs.py ΓÇö Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi & Tß╗▒ ─æß╗Öng li├¬n kß║┐t C╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt (SCRUM-104)

Mß╗Ñc ti├¬u:
- Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi ngay tr├¬n ─æiß╗çn thoß║íi (mobile-friendly REST API)
- Tß╗▒ ─æß╗Öng li├¬n kß║┐t vß╗¢i C╞í hß╗Öi kinh doanh ─æang mß╗ƒ gß║ºn nhß║Ñt cß╗ºa kh├ích h├áng m├á nh├ón vi├¬n c├│ quyß╗ün truy cß║¡p
- Kiß╗âm tra t├¡nh hß╗úp lß╗ç: c╞í hß╗Öi ─æ╞░ß╗úc chß╗ìn phß║úi thuß╗Öc kh├ích h├áng ─æ├ú chß╗ìn
- Quß║ún l├╜ lß╗ïch gß╗ìi lß║íi v├á tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc (task) gß╗ìi lß║íi chß╗æng tß║ío tr├╣ng lß║╖p
- Lß║Ñy lß╗ïch sß╗¡ cuß╗Öc gß╗ìi theo kh├ích h├áng vß╗¢i ph├ón trang v├á bß╗Ö lß╗ìc n├óng cao
"""
from __future__ import annotations

import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db
from app.tasks_reminders import create_task, ensure_tasks_tables

# Danh mß╗Ñc kß║┐t quß║ú cuß╗Öc gß╗ìi chuß║⌐n h├│a (M├ú chuß║⌐n -> Nh├ún hiß╗ân thß╗ï)
VALID_CALL_RESULTS = {
    "connected": "─É├ú li├¬n hß╗ç th├ánh c├┤ng",
    "no_answer": "Kh├┤ng nghe m├íy",
    "callback_requested": "Hß║╣n gß╗ìi lß║íi",
    "interested": "Kh├ích h├áng quan t├óm",
    "not_interested": "Kh├ích h├áng ch╞░a c├│ nhu cß║ºu",
    "busy": "M├íy bß║¡n",
    "wrong_number": "Sai sß╗æ ─æiß╗çn thoß║íi",
    "other": "Kh├íc",
}

# Map ng╞░ß╗úc nh├ún tiß║┐ng Viß╗çt -> m├ú chuß║⌐n ─æß╗â hß╗ù trß╗ú cß║ú 2 c├ích gß╗¡i tß╗½ mobile
_LABEL_TO_CODE = {v.lower(): k for k, v in VALID_CALL_RESULTS.items()}


def normalize_call_result(result_input: str) -> str:
    """Chuß║⌐n h├│a kß║┐t quß║ú cuß╗Öc gß╗ìi vß╗ü m├ú code hß╗úp lß╗ç hoß║╖c n├⌐m ValueError nß║┐u kh├┤ng hß╗úp lß╗ç."""
    if not result_input or not result_input.strip():
        raise ValueError("Vui l├▓ng chß╗ìn kß║┐t quß║ú cuß╗Öc gß╗ìi.")

    cleaned = result_input.strip().lower()
    if cleaned in VALID_CALL_RESULTS:
        return cleaned
    if cleaned in _LABEL_TO_CODE:
        return _LABEL_TO_CODE[cleaned]

    # Kiß╗âm tra xem c├│ khß╗¢p nh├ún viß║┐t hoa kh├┤ng
    for code, label in VALID_CALL_RESULTS.items():
        if label.lower() == cleaned or code == cleaned:
            return code

    valid_options = ", ".join([f"'{k}' ({v})" for k, v in VALID_CALL_RESULTS.items()])
    raise ValueError(f"Kß║┐t quß║ú cuß╗Öc gß╗ìi '{result_input}' kh├┤ng hß╗úp lß╗ç. C├íc kß║┐t quß║ú hß╗úp lß╗ç: {valid_options}")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    name = getattr(type(conn), "__name__", "").lower()
    return "sqlite" in mod or "sqlite" in name


def ensure_call_logs_table(conn) -> None:
    """Tß╗▒ ─æß╗Öng khß╗ƒi tß║ío bß║úng dbo.call_logs nß║┐u ch╞░a tß╗ôn tß║íi."""
    ensure_tasks_tables(conn)
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS call_logs (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id       INTEGER NOT NULL,
                opportunity_id    INTEGER NULL,
                user_id           INTEGER NOT NULL,
                call_result       TEXT NOT NULL,
                notes             TEXT NULL,
                called_at         INTEGER NOT NULL,
                callback_at       INTEGER NULL,
                callback_task_id  INTEGER NULL,
                created_at        INTEGER NOT NULL,
                updated_at        INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_call_logs_customer_called_at
            ON call_logs (customer_id, called_at DESC);
            """
        )
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'call_logs' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.call_logs (
                id                BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
                customer_id       INT            NOT NULL,
                opportunity_id    INT            NULL,
                user_id           INT            NOT NULL,
                call_result       NVARCHAR(100)  NOT NULL,
                notes             NVARCHAR(1000) NULL,
                called_at         BIGINT         NOT NULL,
                callback_at       BIGINT         NULL,
                callback_task_id  INT            NULL,
                created_at        BIGINT         NOT NULL,
                updated_at        BIGINT         NOT NULL,
                CONSTRAINT FK_call_logs_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE,
                CONSTRAINT FK_call_logs_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id),
                CONSTRAINT FK_call_logs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
                CONSTRAINT FK_call_logs_task FOREIGN KEY (callback_task_id) REFERENCES dbo.tasks(id)
            );
            CREATE INDEX IX_call_logs_customer_called_at ON dbo.call_logs (customer_id, called_at DESC);
            CREATE INDEX IX_call_logs_user_called_at ON dbo.call_logs (user_id, called_at DESC);
            CREATE INDEX IX_call_logs_opportunity ON dbo.call_logs (opportunity_id);
        END
        """
    )
    conn.commit()


def find_nearest_open_opportunity(
    conn: Any,
    customer_id: int,
    user_id: int,
    user_role: str = "employee",
) -> dict[str, Any] | None:
    """
    T├¼m c╞í hß╗Öi kinh doanh ─æang mß╗ƒ gß║ºn nhß║Ñt cß╗ºa kh├ích h├áng m├á nh├ón vi├¬n c├│ quyß╗ün truy cß║¡p:
    - C╞í hß╗Öi ─æang mß╗ƒ: stage kh├┤ng thuß╗Öc trß║íng th├íi ─æ├│ng/hß╗ºy ('won', 'lost', '─É├│ng th├ánh c├┤ng', 'Thß║Ñt bß║íi', '─É├ú hß╗ºy').
    - Quyß╗ün truy cß║¡p: nh├ón vi├¬n l├á chß╗º sß╗ƒ hß╗»u, ng╞░ß╗¥i tß║ío, th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗, hoß║╖c c├│ vai tr├▓ manager/admin.
    - ╞»u ti├¬n: thß╗¥i ─æiß╗âm cß║¡p nhß║¡t hoß║╖c tß║ío mß╗¢i gß║ºn nhß║Ñt (updated_at DESC, created_at DESC).
    """
    closed_stages = ("won", "lost", "─æ├│ng th├ánh c├┤ng", "thß║Ñt bß║íi", "─æ├ú hß╗ºy", "closed_won", "closed_lost")
    placeholders = ",".join(["?"] * len(closed_stages))

    where_clauses = [
        "o.customer_id = ?",
        f"LOWER(o.stage) NOT IN ({placeholders})",
    ]
    params: list[Any] = [customer_id, *closed_stages]

    # Kiß╗âm tra ph├ón quyß╗ün truy cß║¡p nß║┐u l├á nh├ón vi├¬n th├┤ng th╞░ß╗¥ng
    if user_role not in {"admin", "manager"}:
        where_clauses.append(
            """
            (
                o.created_by = ?
                OR o.owner_id = ?
                OR EXISTS (
                    SELECT 1 FROM dbo.opportunity_shares os
                    WHERE os.opportunity_id = o.id AND os.user_id = ?
                )
            )
            """
        )
        params.extend([user_id, user_id, user_id])

    where_sql = " AND ".join(where_clauses)
    query = f"""
        SELECT o.id, o.title, o.stage, o.value, o.customer_id, o.updated_at, o.created_at
        FROM dbo.opportunities o
        WHERE {where_sql}
        ORDER BY o.updated_at DESC, o.created_at DESC
    """
    rows = fetch_all(conn, query, params)
    return rows[0] if rows else None


def record_call_log(
    customer_id: int,
    call_result: str,
    user_id: int,
    user_role: str = "employee",
    notes: str = "",
    opportunity_id: int | None = None,
    called_at: int | None = None,
    callback_at: int | None = None,
    conn: Any = None,
) -> dict[str, Any]:
    """
    Ghi nhß║¡n mß╗Öt cuß╗Öc gß╗ìi nhanh tß╗½ mobile / web:
    - Kiß╗âm tra kh├ích h├áng tß╗ôn tß║íi.
    - Chuß║⌐n h├│a kß║┐t quß║ú cuß╗Öc gß╗ìi.
    - Kiß╗âm tra ghi ch├║ kh├┤ng v╞░ß╗út qu├í 1000 k├╜ tß╗▒.
    - Nß║┐u c├│ truyß╗ün opportunity_id: x├íc minh c╞í hß╗Öi thuß╗Öc ─æ├║ng kh├ích h├áng.
    - Nß║┐u kh├┤ng truyß╗ün: tß╗▒ ─æß╗Öng li├¬n kß║┐t vß╗¢i c╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt cß╗ºa kh├ích h├áng m├á nh├ón vi├¬n c├│ quyß╗ün.
    - Nß║┐u c├│ callback_at: tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc gß╗ìi lß║íi trong dbo.tasks (chß╗æng tr├╣ng lß║╖p).
    """
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    # 1. Kiß╗âm tra kh├ích h├áng
    cust = fetch_one(conn, "SELECT id, name FROM dbo.customers WHERE id = ?", (customer_id,))
    if not cust:
        raise ValueError("Kh├ích h├áng kh├┤ng tß╗ôn tß║íi.")
    customer_name = str(cust.get("name") or f"#{customer_id}")

    # 2. Chuß║⌐n h├│a kß║┐t quß║ú cuß╗Öc gß╗ìi
    norm_result = normalize_call_result(call_result)

    # 3. Kiß╗âm tra ghi ch├║
    clean_notes = notes.strip() if notes else ""
    if len(clean_notes) > 1000:
        raise ValueError("Ghi ch├║ cuß╗Öc gß╗ìi kh├┤ng ─æ╞░ß╗úc v╞░ß╗út qu├í 1000 k├╜ tß╗▒.")

    # 4. X├íc ─æß╗ïnh c╞í hß╗Öi kinh doanh li├¬n quan
    final_opp_id: int | None = None
    if opportunity_id:
        opp_row = fetch_one(conn, "SELECT id, customer_id, title FROM dbo.opportunities WHERE id = ?", (opportunity_id,))
        if not opp_row:
            raise ValueError("C╞í hß╗Öi kinh doanh kh├┤ng tß╗ôn tß║íi.")
        if int(opp_row["customer_id"]) != customer_id:
            raise ValueError("C╞í hß╗Öi kinh doanh kh├┤ng thuß╗Öc kh├ích h├áng ─æ├ú chß╗ìn.")
        final_opp_id = int(opp_row["id"])
    else:
        # Tß╗▒ ─æß╗Öng t├¼m c╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt
        nearest_opp = find_nearest_open_opportunity(conn, customer_id, user_id=user_id, user_role=user_role)
        if nearest_opp:
            final_opp_id = int(nearest_opp["id"])

    # 5. Thß╗¥i ─æiß╗âm cuß╗Öc gß╗ìi
    now = _now_ms()
    final_called_at = called_at if called_at and called_at > 0 else now

    # 6. Kiß╗âm tra thß╗¥i ─æiß╗âm gß╗ìi lß║íi nß║┐u c├│
    final_callback_at: int | None = None
    callback_task_id: int | None = None

    if callback_at:
        try:
            cb_val = int(callback_at)
            if cb_val > 0:
                final_callback_at = cb_val
        except (ValueError, TypeError):
            raise ValueError("Thß╗¥i ─æiß╗âm gß╗ìi lß║íi kh├┤ng hß╗úp lß╗ç.")

    # 7. Tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc gß╗ìi lß║íi (callback task) nß║┐u c├│ lß╗ïch gß╗ìi lß║íi
    if final_callback_at:
        task_title = f"Gß╗ìi lß║íi cho kh├ích h├áng: {customer_name}"
        task_desc = f"Cuß╗Öc gß╗ìi l├║c {time.strftime('%d/%m/%Y %H:%M', time.gmtime(final_called_at / 1000))}. Kß║┐t quß║ú: {VALID_CALL_RESULTS[norm_result]}. Ghi ch├║: {clean_notes}"
        priority = "high" if norm_result in {"callback_requested", "interested"} else "medium"

        # Kiß╗âm tra xem ─æ├ú c├│ task t╞░╞íng tß╗▒ ch╞░a ─æß╗â chß╗æng tß║ío tr├╣ng do mß║íng chß║¡p chß╗¥n
        existing_task = fetch_one(
            conn,
            """
            SELECT id FROM dbo.tasks
            WHERE customer_id = ? AND assigned_to = ? AND due_date = ? AND title = ? AND status = 'pending'
            """,
            (customer_id, user_id, final_callback_at, task_title),
        )
        if existing_task:
            callback_task_id = int(existing_task["id"])
        else:
            task_data = create_task(
                title=task_title,
                due_date=final_callback_at,
                assigned_to=user_id,
                created_by=user_id,
                description=task_desc,
                customer_id=customer_id,
                opportunity_id=final_opp_id,
                priority=priority,
                status="pending",
                conn=conn,
            )
            callback_task_id = int(task_data["id"]) if task_data else None

    # 8. L╞░u bß║ún ghi cuß╗Öc gß╗ìi v├áo dbo.call_logs
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.call_logs
            (customer_id, opportunity_id, user_id, call_result, notes, called_at,
             callback_at, callback_task_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            final_opp_id,
            user_id,
            norm_result,
            clean_notes or None,
            final_called_at,
            final_callback_at,
            callback_task_id,
            now,
            now,
        ),
    )

    if _is_sqlite(conn):
        call_id = cur.lastrowid
    else:
        id_row = fetch_one(conn, "SELECT @@IDENTITY AS id")
        call_id = int(id_row["id"]) if id_row and id_row.get("id") else 0
    conn.commit()

    return get_call_log_by_id(call_id, conn=conn)  # type: ignore


def get_call_log_by_id(call_id: int, conn: Any = None) -> dict[str, Any] | None:
    """Lß║Ñy chi tiß║┐t bß║ún ghi cuß╗Öc gß╗ìi theo ID."""
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    row = fetch_one(
        conn,
        """
        SELECT cl.id, cl.customer_id, c.name AS customer_name,
               cl.opportunity_id, o.title AS opportunity_title,
               cl.user_id, u.full_name AS caller_name,
               cl.call_result, cl.notes, cl.called_at, cl.callback_at,
               cl.callback_task_id, cl.created_at, cl.updated_at
        FROM dbo.call_logs cl
        LEFT JOIN dbo.customers c ON cl.customer_id = c.id
        LEFT JOIN dbo.opportunities o ON cl.opportunity_id = o.id
        LEFT JOIN dbo.users u ON cl.user_id = u.id
        WHERE cl.id = ?
        """,
        (call_id,),
    )
    if not row:
        return None

    res_code = str(row["call_result"])
    return {
        "id": int(row["id"]),
        "customer_id": int(row["customer_id"]),
        "customer_name": str(row.get("customer_name") or ""),
        "opportunity_id": row["opportunity_id"],
        "opportunity_title": str(row.get("opportunity_title") or ""),
        "user_id": int(row["user_id"]),
        "caller_name": str(row.get("caller_name") or ""),
        "call_result": res_code,
        "call_result_label": VALID_CALL_RESULTS.get(res_code, res_code),
        "notes": row.get("notes") or "",
        "called_at": int(row["called_at"]),
        "callback_at": row.get("callback_at"),
        "callback_task_id": row.get("callback_task_id"),
        "created_at": int(row["created_at"]),
        "updated_at": int(row["updated_at"]),
    }


def update_call_log(
    call_id: int,
    user_id: int,
    user_role: str = "employee",
    notes: str | None = None,
    call_result: str | None = None,
    callback_at: int | None = None,
    conn: Any = None,
) -> dict[str, Any] | None:
    """Cß║¡p nhß║¡t ghi ch├║ hoß║╖c kß║┐t quß║ú cuß╗Öc gß╗ìi."""
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    call_row = get_call_log_by_id(call_id, conn=conn)
    if not call_row:
        raise LookupError("Kh├┤ng t├¼m thß║Ñy bß║ún ghi cuß╗Öc gß╗ìi.")

    # Ph├ón quyß╗ün: chß╗ë ng╞░ß╗¥i thß╗▒c hiß╗çn hoß║╖c manager/admin mß╗¢i ─æ╞░ß╗úc sß╗¡a
    if user_role not in {"admin", "manager"} and call_row["user_id"] != user_id:
        raise PermissionError("Bß║ín kh├┤ng c├│ quyß╗ün sß╗¡a bß║ún ghi cuß╗Öc gß╗ìi cß╗ºa ng╞░ß╗¥i kh├íc.")

    updates = []
    params: list[Any] = []

    if notes is not None:
        clean_notes = notes.strip()
        if len(clean_notes) > 1000:
            raise ValueError("Ghi ch├║ cuß╗Öc gß╗ìi kh├┤ng ─æ╞░ß╗úc v╞░ß╗út qu├í 1000 k├╜ tß╗▒.")
        updates.append("notes = ?")
        params.append(clean_notes)

    if call_result is not None:
        norm_res = normalize_call_result(call_result)
        updates.append("call_result = ?")
        params.append(norm_res)

    if callback_at is not None:
        updates.append("callback_at = ?")
        params.append(callback_at)

    now = _now_ms()
    updates.append("updated_at = ?")
    params.append(now)

    params.append(call_id)
    cur = conn.cursor()
    cur.execute(f"UPDATE dbo.call_logs SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()

    return get_call_log_by_id(call_id, conn=conn)


def list_customer_call_history(
    customer_id: int,
    user_id: int | None = None,
    call_result: str | None = None,
    from_date: int | None = None,
    to_date: int | None = None,
    page: int = 1,
    per_page: int = 20,
    conn: Any = None,
) -> dict[str, Any]:
    """Lß║Ñy danh s├ích lß╗ïch sß╗¡ cuß╗Öc gß╗ìi cß╗ºa kh├ích h├áng vß╗¢i ph├ón trang v├á bß╗Ö lß╗ìc."""
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    where_clauses = ["cl.customer_id = ?"]
    params: list[Any] = [customer_id]

    if user_id:
        where_clauses.append("cl.user_id = ?")
        params.append(user_id)

    if call_result:
        clean_res = call_result.strip().lower()
        if clean_res in VALID_CALL_RESULTS:
            where_clauses.append("cl.call_result = ?")
            params.append(clean_res)
        elif clean_res in _LABEL_TO_CODE:
            where_clauses.append("cl.call_result = ?")
            params.append(_LABEL_TO_CODE[clean_res])

    if from_date:
        where_clauses.append("cl.called_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("cl.called_at <= ?")
        params.append(to_date)

    where_sql = " AND ".join(where_clauses)
    count_row = fetch_one(conn, f"SELECT COUNT(*) AS total FROM dbo.call_logs cl WHERE {where_sql}", params)
    total = int(count_row["total"]) if count_row else 0

    offset = (page - 1) * per_page
    rows = fetch_all(
        conn,
        f"""
        SELECT cl.id, cl.customer_id, c.name AS customer_name,
               cl.opportunity_id, o.title AS opportunity_title,
               cl.user_id, u.full_name AS caller_name,
               cl.call_result, cl.notes, cl.called_at, cl.callback_at,
               cl.callback_task_id, cl.created_at, cl.updated_at
        FROM dbo.call_logs cl
        LEFT JOIN dbo.customers c ON cl.customer_id = c.id
        LEFT JOIN dbo.opportunities o ON cl.opportunity_id = o.id
        LEFT JOIN dbo.users u ON cl.user_id = u.id
        WHERE {where_sql}
        ORDER BY cl.called_at DESC
        """,
        params,
    )

    paged_rows = rows[offset : offset + per_page]
    items = []
    for r in paged_rows:
        res_code = str(r["call_result"])
        items.append(
            {
                "id": int(r["id"]),
                "customer_id": int(r["customer_id"]),
                "customer_name": str(r.get("customer_name") or ""),
                "opportunity_id": r["opportunity_id"],
                "opportunity_title": str(r.get("opportunity_title") or ""),
                "user_id": int(r["user_id"]),
                "caller_name": str(r.get("caller_name") or ""),
                "call_result": res_code,
                "call_result_label": VALID_CALL_RESULTS.get(res_code, res_code),
                "notes": r.get("notes") or "",
                "called_at": int(r["called_at"]),
                "callback_at": r.get("callback_at"),
                "callback_task_id": r.get("callback_task_id"),
                "created_at": int(r["created_at"]),
                "updated_at": int(r["updated_at"]),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }
