"""
app/opportunity_history.py — Quản lý Lịch sử thay đổi Cơ hội kinh doanh (SCRUM-95)

Theo dõi các trường thay đổi:
- stage: Giai đoạn kinh doanh
- value: Giá trị cơ hội
- expected_close_date: Ngày chốt dự kiến
- owner: Người sở hữu cơ hội (owner_id)

Quy tắc:
- Ghi lịch sử trong cùng transaction với cập nhật cơ hội.
- Chỉ ghi khi giá trị thực sự thay đổi.
- Xác định changed_by từ thông tin xác thực backend (CurrentUser.id).
- Không cho Client tự tạo/sửa/xóa bản ghi lịch sử qua API.
"""
from __future__ import annotations

import datetime
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db

FIELD_LABELS: dict[str, str] = {
    "stage": "Giai đoạn",
    "value": "Giá trị cơ hội",
    "expected_close_date": "Ngày chốt dự kiến",
    "owner": "Người sở hữu",
}

TRACKED_FIELDS = {"stage", "value", "expected_close_date", "owner"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _format_iso(ms: int | None) -> str:
    if not ms:
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(ms / 1000.0, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    return "sqlite" in mod or hasattr(conn, "isolation_level")


def ensure_opportunity_history_table(conn) -> None:
    """Đảm bảo bảng dbo.opportunity_history và cột owner_id trong dbo.opportunities tồn tại."""
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunity_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id  INTEGER NOT NULL,
                field_name      TEXT NOT NULL,
                old_value       TEXT NULL,
                new_value       TEXT NULL,
                changed_by      INTEGER NOT NULL,
                changed_at      INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_opp_hist_opp_id_changed_at
            ON opportunity_history (opportunity_id, changed_at DESC);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_opp_hist_field_name
            ON opportunity_history (opportunity_id, field_name);
            """
        )
        # Kiểm tra cột owner_id trong opportunities (nếu là sqlite)
        try:
            cur.execute("ALTER TABLE opportunities ADD COLUMN owner_id INTEGER;")
        except Exception:
            pass
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'opportunity_history' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.opportunity_history (
                id              BIGINT          IDENTITY(1,1) PRIMARY KEY,
                opportunity_id  INT             NOT NULL,
                field_name      NVARCHAR(100)   NOT NULL,
                old_value       NVARCHAR(MAX)   NULL,
                new_value       NVARCHAR(MAX)   NULL,
                changed_by      INT             NOT NULL,
                changed_at      BIGINT          NOT NULL,
                CONSTRAINT FK_opp_hist_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
                CONSTRAINT FK_opp_hist_user FOREIGN KEY (changed_by) REFERENCES dbo.users(id)
            );
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.opportunity_history') AND name = N'IX_opp_hist_opp_id_changed_at')
        BEGIN
            CREATE INDEX IX_opp_hist_opp_id_changed_at ON dbo.opportunity_history (opportunity_id, changed_at DESC);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.opportunity_history') AND name = N'IX_opp_hist_field_name')
        BEGIN
            CREATE INDEX IX_opp_hist_field_name ON dbo.opportunity_history (opportunity_id, field_name);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'owner_id')
        BEGIN
            ALTER TABLE dbo.opportunities ADD owner_id INT NULL;
        END
        """
    )
    conn.commit()


def can_access_opportunity(user: Any, opportunity: dict[str, Any]) -> bool:
    """
    Kiểm tra quyền truy cập cơ hội và lịch sử:
    - Admin & Manager: Toàn quyền xem tất cả.
    - Employee: Chỉ xem cơ hội do mình tạo hoặc sở hữu.
    """
    if not user:
        return False
    role = getattr(user, "role", "")
    if role in {"admin", "manager"}:
        return True

    user_id = getattr(user, "id", None)
    if user_id is None:
        return False

    opp_owner = opportunity.get("owner_id")
    opp_creator = opportunity.get("created_by")

    # Nếu người dùng là người tạo hoặc là người sở hữu
    if opp_owner is not None and int(opp_owner) == int(user_id):
        return True
    if opp_creator is not None and int(opp_creator) == int(user_id):
        return True

    # Kiểm tra nếu người dùng được chia sẻ cơ hội (SCRUM-97)
    if "id" in opportunity:
        try:
            conn = get_db()
            shares_table = "dbo.opportunity_shares" if not _is_sqlite(conn) else "opportunity_shares"
            share_row = fetch_one(
                conn,
                f"SELECT 1 FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?",
                (opportunity["id"], int(user_id)),
            )
            if share_row:
                return True
        except Exception:
            pass

    return False


def compute_opportunity_diff(
    old_opp: dict[str, Any],
    new_stage: str,
    new_value: float,
    new_expected_close_date: str,
    new_owner_id: int | None,
) -> list[dict[str, Any]]:
    """
    So sánh giá trị cũ và mới của 4 trường nghiệp vụ yêu cầu (SCRUM-95):
    - stage
    - value
    - expected_close_date
    - owner
    Chỉ trả về những trường thực sự thay đổi.
    """
    diffs: list[dict[str, Any]] = []

    # 1. Stage
    old_stage = (old_opp.get("stage") or "").strip()
    clean_new_stage = (new_stage or "").strip()
    if clean_new_stage and old_stage != clean_new_stage:
        diffs.append({
            "field_name": "stage",
            "old_value": old_stage,
            "new_value": clean_new_stage,
        })

    # 2. Value
    try:
        old_val = float(old_opp.get("value") or 0.0)
    except (ValueError, TypeError):
        old_val = 0.0
    try:
        n_val = float(new_value)
    except (ValueError, TypeError):
        n_val = 0.0

    if abs(old_val - n_val) > 0.0001:
        # Làm sạch chuỗi hiển thị số (tránh định dạng khoa học e+08)
        old_str = str(int(old_val)) if old_val == int(old_val) else f"{old_val:.2f}".rstrip("0").rstrip(".")
        new_str = str(int(n_val)) if n_val == int(n_val) else f"{n_val:.2f}".rstrip("0").rstrip(".")
        diffs.append({
            "field_name": "value",
            "old_value": old_str,
            "new_value": new_str,
        })

    # 3. Expected Close Date
    old_date = (old_opp.get("expected_close_date") or "").strip()
    clean_new_date = (new_expected_close_date or "").strip()
    if old_date != clean_new_date:
        diffs.append({
            "field_name": "expected_close_date",
            "old_value": old_date if old_date else None,
            "new_value": clean_new_date if clean_new_date else None,
        })

    # 4. Owner
    if new_owner_id is not None:
        raw_old_owner = old_opp.get("owner_id")
        if raw_old_owner is None:
            raw_old_owner = old_opp.get("created_by")
        try:
            old_owner_int = int(raw_old_owner) if raw_old_owner is not None else None
        except (ValueError, TypeError):
            old_owner_int = None

        try:
            new_owner_int = int(new_owner_id)
        except (ValueError, TypeError):
            new_owner_int = None

        if new_owner_int is not None and old_owner_int != new_owner_int:
            diffs.append({
                "field_name": "owner",
                "old_value": str(old_owner_int) if old_owner_int is not None else None,
                "new_value": str(new_owner_int),
            })

    return diffs


def record_history_in_transaction(
    conn,
    opportunity_id: int,
    diffs: list[dict[str, Any]],
    changed_by: int,
    changed_at: int | None = None,
) -> None:
    """Ghi danh sách thay đổi vào bảng opportunity_history trong cùng transaction."""
    if not diffs:
        return

    now = changed_at if changed_at is not None else _now_ms()
    cur = conn.cursor()

    table_name = "dbo.opportunity_history" if not _is_sqlite(conn) else "opportunity_history"
    insert_sql = f"""
        INSERT INTO {table_name}
        (opportunity_id, field_name, old_value, new_value, changed_by, changed_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    for diff in diffs:
        cur.execute(
            insert_sql,
            (
                opportunity_id,
                diff["field_name"],
                str(diff["old_value"]) if diff["old_value"] is not None else None,
                str(diff["new_value"]) if diff["new_value"] is not None else None,
                int(changed_by),
                now,
            ),
        )


def get_opportunity_history(
    opportunity_id: int,
    field: str = "",
    page: int = 1,
    page_size: int = 20,
    conn: Any = None,
) -> dict[str, Any]:
    """
    Lấy danh sách lịch sử thay đổi của một cơ hội (hỗ trợ phân trang và lọc theo field).
    """
    db_conn = conn or get_db()
    ensure_opportunity_history_table(db_conn)

    where_clauses = ["h.opportunity_id = ?"]
    params: list[Any] = [opportunity_id]

    clean_field = field.strip().lower()
    if clean_field:
        where_clauses.append("LOWER(h.field_name) = ?")
        params.append(clean_field)

    where_sql = " AND ".join(where_clauses)

    table_name = "dbo.opportunity_history" if not _is_sqlite(db_conn) else "opportunity_history"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM {table_name} h
        WHERE {where_sql}
    """
    count_row = fetch_one(db_conn, count_sql, params)
    total = count_row["total"] if count_row else 0

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    if _is_sqlite(db_conn):
        items_sql = f"""
            SELECT h.id, h.opportunity_id, h.field_name, h.old_value, h.new_value,
                   h.changed_by, u.full_name AS changed_by_name, u.email AS changed_by_email,
                   h.changed_at
            FROM {table_name} h
            LEFT JOIN {users_table} u ON h.changed_by = u.id
            WHERE {where_sql}
            ORDER BY h.changed_at DESC, h.id DESC
            LIMIT ? OFFSET ?
        """
        query_params = params + [page_size, offset]
    else:
        items_sql = f"""
            SELECT h.id, h.opportunity_id, h.field_name, h.old_value, h.new_value,
                   h.changed_by, u.full_name AS changed_by_name, u.email AS changed_by_email,
                   h.changed_at
            FROM {table_name} h
            LEFT JOIN {users_table} u ON h.changed_by = u.id
            WHERE {where_sql}
            ORDER BY h.changed_at DESC, h.id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        query_params = params + [offset, page_size]

    raw_items = fetch_all(db_conn, items_sql, query_params)

    items = []
    for r in raw_items:
        fname = r.get("field_name") or ""
        items.append({
            "id": r.get("id"),
            "opportunity_id": r.get("opportunity_id"),
            "field_name": fname,
            "field_label": FIELD_LABELS.get(fname.lower(), fname),
            "old_value": r.get("old_value"),
            "new_value": r.get("new_value"),
            "changed_by": r.get("changed_by"),
            "changed_by_name": r.get("changed_by_name") or f"User #{r.get('changed_by')}",
            "changed_by_email": r.get("changed_by_email") or "",
            "changed_at": r.get("changed_at"),
            "changed_at_iso": _format_iso(r.get("changed_at")),
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
