"""
app/call_logs.py — Ghi nhanh kết quả cuộc gọi & Tự động liên kết Cơ hội mở gần nhất (SCRUM-104)

Mục tiêu:
- Ghi nhanh kết quả cuộc gọi ngay trên điện thoại (mobile-friendly REST API)
- Tự động liên kết với Cơ hội kinh doanh đang mở gần nhất của khách hàng mà nhân viên có quyền truy cập
- Kiểm tra tính hợp lệ: cơ hội được chọn phải thuộc khách hàng đã chọn
- Quản lý lịch gọi lại và tự động tạo công việc (task) gọi lại chống tạo trùng lặp
- Lấy lịch sử cuộc gọi theo khách hàng với phân trang và bộ lọc nâng cao
"""
from __future__ import annotations

import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db
from app.tasks_reminders import create_task, ensure_tasks_tables

# Danh mục kết quả cuộc gọi chuẩn hóa (Mã chuẩn -> Nhãn hiển thị)
VALID_CALL_RESULTS = {
    "connected": "Đã liên hệ thành công",
    "no_answer": "Không nghe máy",
    "callback_requested": "Hẹn gọi lại",
    "interested": "Khách hàng quan tâm",
    "not_interested": "Khách hàng chưa có nhu cầu",
    "busy": "Máy bận",
    "wrong_number": "Sai số điện thoại",
    "other": "Khác",
}

# Map ngược nhãn tiếng Việt -> mã chuẩn để hỗ trợ cả 2 cách gửi từ mobile
_LABEL_TO_CODE = {v.lower(): k for k, v in VALID_CALL_RESULTS.items()}


def normalize_call_result(result_input: str) -> str:
    """Chuẩn hóa kết quả cuộc gọi về mã code hợp lệ hoặc ném ValueError nếu không hợp lệ."""
    if not result_input or not result_input.strip():
        raise ValueError("Vui lòng chọn kết quả cuộc gọi.")

    cleaned = result_input.strip().lower()
    if cleaned in VALID_CALL_RESULTS:
        return cleaned
    if cleaned in _LABEL_TO_CODE:
        return _LABEL_TO_CODE[cleaned]

    # Kiểm tra xem có khớp nhãn viết hoa không
    for code, label in VALID_CALL_RESULTS.items():
        if label.lower() == cleaned or code == cleaned:
            return code

    valid_options = ", ".join([f"'{k}' ({v})" for k, v in VALID_CALL_RESULTS.items()])
    raise ValueError(f"Kết quả cuộc gọi '{result_input}' không hợp lệ. Các kết quả hợp lệ: {valid_options}")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    name = getattr(type(conn), "__name__", "").lower()
    return "sqlite" in mod or "sqlite" in name


def ensure_call_logs_table(conn) -> None:
    """Tự động khởi tạo bảng dbo.call_logs nếu chưa tồn tại."""
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
    Tìm cơ hội kinh doanh đang mở gần nhất của khách hàng mà nhân viên có quyền truy cập:
    - Cơ hội đang mở: stage không thuộc trạng thái đóng/hủy ('won', 'lost', 'Đóng thành công', 'Thất bại', 'Đã hủy').
    - Quyền truy cập: nhân viên là chủ sở hữu, người tạo, thành viên được chia sẻ, hoặc có vai trò manager/admin.
    - Ưu tiên: thời điểm cập nhật hoặc tạo mới gần nhất (updated_at DESC, created_at DESC).
    """
    closed_stages = ("won", "lost", "đóng thành công", "thất bại", "đã hủy", "closed_won", "closed_lost")
    placeholders = ",".join(["?"] * len(closed_stages))

    where_clauses = [
        "o.customer_id = ?",
        f"LOWER(o.stage) NOT IN ({placeholders})",
    ]
    params: list[Any] = [customer_id, *closed_stages]

    # Kiểm tra phân quyền truy cập nếu là nhân viên thông thường
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
    Ghi nhận một cuộc gọi nhanh từ mobile / web:
    - Kiểm tra khách hàng tồn tại.
    - Chuẩn hóa kết quả cuộc gọi.
    - Kiểm tra ghi chú không vượt quá 1000 ký tự.
    - Nếu có truyền opportunity_id: xác minh cơ hội thuộc đúng khách hàng.
    - Nếu không truyền: tự động liên kết với cơ hội mở gần nhất của khách hàng mà nhân viên có quyền.
    - Nếu có callback_at: tự động tạo công việc gọi lại trong dbo.tasks (chống trùng lặp).
    """
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    # 1. Kiểm tra khách hàng
    cust = fetch_one(conn, "SELECT id, name FROM dbo.customers WHERE id = ?", (customer_id,))
    if not cust:
        raise ValueError("Khách hàng không tồn tại.")
    customer_name = str(cust.get("name") or f"#{customer_id}")

    # 2. Chuẩn hóa kết quả cuộc gọi
    norm_result = normalize_call_result(call_result)

    # 3. Kiểm tra ghi chú
    clean_notes = notes.strip() if notes else ""
    if len(clean_notes) > 1000:
        raise ValueError("Ghi chú cuộc gọi không được vượt quá 1000 ký tự.")

    # 4. Xác định cơ hội kinh doanh liên quan
    final_opp_id: int | None = None
    if opportunity_id:
        opp_row = fetch_one(conn, "SELECT id, customer_id, title FROM dbo.opportunities WHERE id = ?", (opportunity_id,))
        if not opp_row:
            raise ValueError("Cơ hội kinh doanh không tồn tại.")
        if int(opp_row["customer_id"]) != customer_id:
            raise ValueError("Cơ hội kinh doanh không thuộc khách hàng đã chọn.")
        final_opp_id = int(opp_row["id"])
    else:
        # Tự động tìm cơ hội mở gần nhất
        nearest_opp = find_nearest_open_opportunity(conn, customer_id, user_id=user_id, user_role=user_role)
        if nearest_opp:
            final_opp_id = int(nearest_opp["id"])

    # 5. Thời điểm cuộc gọi
    now = _now_ms()
    final_called_at = called_at if called_at and called_at > 0 else now

    # 6. Kiểm tra thời điểm gọi lại nếu có
    final_callback_at: int | None = None
    callback_task_id: int | None = None

    if callback_at:
        try:
            cb_val = int(callback_at)
            if cb_val > 0:
                final_callback_at = cb_val
        except (ValueError, TypeError):
            raise ValueError("Thời điểm gọi lại không hợp lệ.")

    # 7. Tự động tạo công việc gọi lại (callback task) nếu có lịch gọi lại
    if final_callback_at:
        task_title = f"Gọi lại cho khách hàng: {customer_name}"
        task_desc = f"Cuộc gọi lúc {time.strftime('%d/%m/%Y %H:%M', time.gmtime(final_called_at / 1000))}. Kết quả: {VALID_CALL_RESULTS[norm_result]}. Ghi chú: {clean_notes}"
        priority = "high" if norm_result in {"callback_requested", "interested"} else "medium"

        # Kiểm tra xem đã có task tương tự chưa để chống tạo trùng do mạng chập chờn
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

    # 8. Lưu bản ghi cuộc gọi vào dbo.call_logs
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
    """Lấy chi tiết bản ghi cuộc gọi theo ID."""
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
    """Cập nhật ghi chú hoặc kết quả cuộc gọi."""
    if conn is None:
        conn = get_db()
    ensure_call_logs_table(conn)

    call_row = get_call_log_by_id(call_id, conn=conn)
    if not call_row:
        raise LookupError("Không tìm thấy bản ghi cuộc gọi.")

    # Phân quyền: chỉ người thực hiện hoặc manager/admin mới được sửa
    if user_role not in {"admin", "manager"} and call_row["user_id"] != user_id:
        raise PermissionError("Bạn không có quyền sửa bản ghi cuộc gọi của người khác.")

    updates = []
    params: list[Any] = []

    if notes is not None:
        clean_notes = notes.strip()
        if len(clean_notes) > 1000:
            raise ValueError("Ghi chú cuộc gọi không được vượt quá 1000 ký tự.")
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
    """Lấy danh sách lịch sử cuộc gọi của khách hàng với phân trang và bộ lọc."""
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
