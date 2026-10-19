"""
app/opportunity_shares.py — Quản lý Chia sẻ & Chuyển quyền Sở hữu Cơ hội kinh doanh (SCRUM-97)

Mục tiêu:
- Duy trì một Primary Owner (người sở hữu chính chịu trách nhiệm)
- Hỗ trợ nhiều Shared Members với các cấp độ quyền: 'read', 'edit', 'manage'
- Cho phép Primary Owner / Manager / Admin chuyển quyền sở hữu chính
- Tích hợp ghi nhận lịch sử thay đổi vào dbo.opportunity_history (SCRUM-95)
"""
from __future__ import annotations

import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db
from app.opportunity_history import ensure_opportunity_history_table, record_history_in_transaction

VALID_PERMISSION_LEVELS = {"read", "edit", "manage"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    return "sqlite" in mod or hasattr(conn, "isolation_level")


def ensure_opportunity_shares_table(conn) -> None:
    """Tự động khởi tạo bảng dbo.opportunity_shares nếu chưa tồn tại."""
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunity_shares (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id      INTEGER NOT NULL,
                user_id             INTEGER NOT NULL,
                shared_by           INTEGER NOT NULL,
                permission_level    TEXT NOT NULL DEFAULT 'read',
                created_at          INTEGER NOT NULL,
                updated_at          INTEGER NOT NULL,
                CONSTRAINT UQ_opp_share_user UNIQUE (opportunity_id, user_id)
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_opp_shares_opp_id
            ON opportunity_shares (opportunity_id);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_opp_shares_user_id
            ON opportunity_shares (user_id);
            """
        )
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'opportunity_shares' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.opportunity_shares (
                id                  BIGINT          IDENTITY(1,1) PRIMARY KEY,
                opportunity_id      INT             NOT NULL,
                user_id             INT             NOT NULL,
                shared_by           INT             NOT NULL,
                permission_level    NVARCHAR(50)    NOT NULL CONSTRAINT DF_opp_share_perm DEFAULT ('read'),
                created_at          BIGINT          NOT NULL,
                updated_at          BIGINT          NOT NULL,
                CONSTRAINT FK_opp_share_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
                CONSTRAINT FK_opp_share_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
                CONSTRAINT FK_opp_share_shared_by FOREIGN KEY (shared_by) REFERENCES dbo.users(id),
                CONSTRAINT UQ_opp_share_user UNIQUE (opportunity_id, user_id)
            );
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.opportunity_shares') AND name = N'IX_opp_shares_opp_id')
        BEGIN
            CREATE INDEX IX_opp_shares_opp_id ON dbo.opportunity_shares (opportunity_id);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.opportunity_shares') AND name = N'IX_opp_shares_user_id')
        BEGIN
            CREATE INDEX IX_opp_shares_user_id ON dbo.opportunity_shares (user_id);
        END
        """
    )
    conn.commit()


def get_user_share_record(opportunity_id: int, user_id: int, conn: Any = None) -> dict[str, Any] | None:
    """Lấy bản ghi chia sẻ của một user đối với cơ hội."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)
    table_name = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"
    return fetch_one(
        db_conn,
        f"SELECT * FROM {table_name} WHERE opportunity_id = ? AND user_id = ?",
        (opportunity_id, user_id),
    )


def check_opportunity_access(
    user: Any,
    opportunity: dict[str, Any],
    required_permission: str = "read",
    conn: Any = None,
) -> tuple[bool, str]:
    """
    Kiểm tra quyền truy cập chi tiết của người dùng đối với cơ hội (SCRUM-97):
    - required_permission: 'read', 'edit', 'share', 'transfer'
    Trả về (is_allowed, error_message).
    """
    if not user:
        return False, "Chưa đăng nhập."

    role = getattr(user, "role", "")
    if role in {"admin", "manager"}:
        return True, ""

    user_id = getattr(user, "id", None)
    if user_id is None:
        return False, "Không xác định danh tính người dùng."

    primary_owner_id = opportunity.get("owner_id")
    if primary_owner_id is None:
        primary_owner_id = opportunity.get("created_by")

    is_primary_owner = (primary_owner_id is not None and int(primary_owner_id) == int(user_id))
    if is_primary_owner:
        # Primary Owner có toàn quyền: xem, sửa, chia sẻ và chuyển quyền sở hữu
        return True, ""

    # Nếu yêu cầu 'transfer' (chuyển quyền sở hữu) thì chỉ Primary Owner, Manager, Admin mới được
    if required_permission == "transfer":
        return False, "Chỉ Người sở hữu chính hoặc Quản trị viên/Trưởng nhóm mới có quyền chuyển quyền sở hữu."

    # Kiểm tra quyền qua bản ghi chia sẻ (Shared Member)
    share = get_user_share_record(opportunity_id=opportunity["id"], user_id=user_id, conn=conn)
    if not share:
        return False, "Bạn không có quyền truy cập cơ hội này."

    perm = (share.get("permission_level") or "read").lower()

    if required_permission == "read":
        return True, ""
    elif required_permission in {"edit", "activity"}:
        if perm in {"edit", "manage"}:
            return True, ""
        return False, "Bạn chỉ có quyền xem, không có quyền chỉnh sửa hoặc ghi nhận hoạt động."
    elif required_permission == "share":
        if perm == "manage":
            return True, ""
        return False, "Bạn không có quyền quản lý chia sẻ cơ hội này."

    return False, "Yêu cầu quyền không hợp lệ."


def list_opportunity_shares(opportunity_id: int, conn: Any = None) -> dict[str, Any]:
    """Lấy thông tin người sở hữu chính và danh sách thành viên được chia sẻ."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"
    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"

    # Lấy thông tin cơ hội và người sở hữu chính
    opp_sql = f"""
        SELECT o.id, o.title, COALESCE(o.owner_id, o.created_by) AS owner_id,
               u.full_name AS owner_name, u.email AS owner_email, u.role AS owner_role
        FROM {opp_table} o
        LEFT JOIN {users_table} u ON COALESCE(o.owner_id, o.created_by) = u.id
        WHERE o.id = ?
    """
    opp = fetch_one(db_conn, opp_sql, (opportunity_id,))
    if not opp:
        raise LookupError("opportunity_not_found")

    primary_owner = {
        "id": opp.get("owner_id"),
        "full_name": opp.get("owner_name") or f"User #{opp.get('owner_id')}",
        "email": opp.get("owner_email") or "",
        "role": opp.get("owner_role") or "",
    }

    # Lấy danh sách thành viên được chia sẻ
    shares_sql = f"""
        SELECT s.id, s.opportunity_id, s.user_id, s.permission_level, s.shared_by,
               s.created_at, s.updated_at,
               u.full_name AS user_name, u.email AS user_email, u.role AS user_role,
               sb.full_name AS shared_by_name
        FROM {shares_table} s
        LEFT JOIN {users_table} u ON s.user_id = u.id
        LEFT JOIN {users_table} sb ON s.shared_by = sb.id
        WHERE s.opportunity_id = ?
        ORDER BY s.id ASC
    """
    shares = fetch_all(db_conn, shares_sql, (opportunity_id,))

    return {
        "opportunity_id": opportunity_id,
        "primary_owner": primary_owner,
        "shares": shares,
    }


def share_opportunity(
    opportunity_id: int,
    user_id: int,
    permission_level: str = "read",
    shared_by: int = 1,
    conn: Any = None,
) -> dict[str, Any]:
    """Chia sẻ cơ hội cho một thành viên mới."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    clean_perm = (permission_level or "read").strip().lower()
    if clean_perm not in VALID_PERMISSION_LEVELS:
        raise ValueError({"message": f"Quyền chia sẻ không hợp lệ. Phải là một trong: {', '.join(VALID_PERMISSION_LEVELS)}"})

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"
    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"

    # Kiểm tra cơ hội tồn tại
    opp = fetch_one(db_conn, f"SELECT id, COALESCE(owner_id, created_by) AS owner_id FROM {opp_table} WHERE id = ?", (opportunity_id,))
    if not opp:
        raise LookupError("opportunity_not_found")

    # Kiểm tra thành viên mục tiêu tồn tại và đang hoạt động
    target_user = fetch_one(db_conn, f"SELECT id, full_name, email, is_active FROM {users_table} WHERE id = ?", (user_id,))
    if not target_user:
        raise ValueError({"message": "Thành viên cần chia sẻ không tồn tại trong hệ thống."})
    if not target_user.get("is_active", True):
        raise ValueError({"message": "Tài khoản của thành viên này đang bị vô hiệu hóa."})

    # Không cho phép chia sẻ với chính Người sở hữu chính
    if int(opp["owner_id"]) == int(user_id):
        raise ValueError({"message": "Không thể chia sẻ cơ hội cho Người sở hữu chính."})

    # Kiểm tra không thêm trùng thành viên
    existing_share = fetch_one(db_conn, f"SELECT id FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?", (opportunity_id, user_id))
    if existing_share:
        raise ValueError({"message": "Thành viên này đã được chia sẻ cơ hội."})

    now = _now_ms()
    cur = db_conn.cursor()
    cur.execute(
        f"""
        INSERT INTO {shares_table} (opportunity_id, user_id, shared_by, permission_level, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (opportunity_id, user_id, shared_by, clean_perm, now, now),
    )
    db_conn.commit()

    return list_opportunity_shares(opportunity_id=opportunity_id, conn=db_conn)


def update_share_permission(
    opportunity_id: int,
    user_id: int,
    permission_level: str,
    updated_by: int = 1,
    conn: Any = None,
) -> dict[str, Any]:
    """Cập nhật quyền chia sẻ của một thành viên."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    clean_perm = (permission_level or "").strip().lower()
    if clean_perm not in VALID_PERMISSION_LEVELS:
        raise ValueError({"message": f"Quyền chia sẻ không hợp lệ. Phải là một trong: {', '.join(VALID_PERMISSION_LEVELS)}"})

    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"
    existing = fetch_one(db_conn, f"SELECT id FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?", (opportunity_id, user_id))
    if not existing:
        raise LookupError("share_not_found")

    now = _now_ms()
    cur = db_conn.cursor()
    cur.execute(
        f"""
        UPDATE {shares_table}
        SET permission_level = ?, updated_at = ?
        WHERE opportunity_id = ? AND user_id = ?
        """,
        (clean_perm, now, opportunity_id, user_id),
    )
    db_conn.commit()

    return list_opportunity_shares(opportunity_id=opportunity_id, conn=db_conn)


def remove_opportunity_share(
    opportunity_id: int,
    user_id: int,
    removed_by: int = 1,
    conn: Any = None,
) -> bool:
    """Gỡ quyền chia sẻ của một thành viên."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"
    existing = fetch_one(db_conn, f"SELECT id FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?", (opportunity_id, user_id))
    if not existing:
        raise LookupError("share_not_found")

    cur = db_conn.cursor()
    cur.execute(f"DELETE FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?", (opportunity_id, user_id))
    db_conn.commit()
    return True


def transfer_opportunity_ownership(
    opportunity_id: int,
    new_owner_id: int,
    transferred_by: int,
    conn: Any = None,
) -> dict[str, Any]:
    """
    Chuyển quyền sở hữu chính của cơ hội (SCRUM-97):
    - Cập nhật owner_id trong dbo.opportunities
    - Xóa new_owner_id khỏi dbo.opportunity_shares (nếu trước đó được chia sẻ)
    - Tự động thêm old_owner_id vào dbo.opportunity_shares với quyền 'edit' để vẫn theo dõi được
    - Ghi nhận lịch sử chuyển quyền sở hữu vào dbo.opportunity_history (SCRUM-95)
    - Toàn bộ chạy trong cùng 1 transaction nguyên tử
    """
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)
    ensure_opportunity_history_table(db_conn)

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"
    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"

    opp = fetch_one(db_conn, f"SELECT id, title, COALESCE(owner_id, created_by) AS owner_id FROM {opp_table} WHERE id = ?", (opportunity_id,))
    if not opp:
        raise LookupError("opportunity_not_found")

    old_owner_id = int(opp["owner_id"])
    if old_owner_id == int(new_owner_id):
        raise ValueError({"message": "Người dùng này hiện đã là Người sở hữu chính của cơ hội."})

    new_owner = fetch_one(db_conn, f"SELECT id, full_name, is_active FROM {users_table} WHERE id = ?", (new_owner_id,))
    if not new_owner:
        raise ValueError({"message": "Chủ sở hữu mới không tồn tại trong hệ thống."})
    if not new_owner.get("is_active", True):
        raise ValueError({"message": "Tài khoản của chủ sở hữu mới đang bị vô hiệu hóa."})

    now = _now_ms()
    cur = db_conn.cursor()
    try:
        # 1. Cập nhật chủ sở hữu mới trong bảng opportunities
        cur.execute(
            f"UPDATE {opp_table} SET owner_id = ?, updated_at = ? WHERE id = ?",
            (new_owner_id, now, opportunity_id),
        )

        # 2. Xóa new_owner_id khỏi bảng shares nếu trước đó là shared member
        cur.execute(
            f"DELETE FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?",
            (opportunity_id, new_owner_id),
        )

        # 3. Thêm old_owner_id vào bảng shares với quyền 'edit' để giữ quyền theo dõi
        old_share_exists = fetch_one(
            db_conn,
            f"SELECT id FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?",
            (opportunity_id, old_owner_id),
        )
        if not old_share_exists:
            cur.execute(
                f"""
                INSERT INTO {shares_table} (opportunity_id, user_id, shared_by, permission_level, created_at, updated_at)
                VALUES (?, ?, ?, 'edit', ?, ?)
                """,
                (opportunity_id, old_owner_id, transferred_by, now, now),
            )

        # 4. Ghi lịch sử chuyển quyền sở hữu vào dbo.opportunity_history (SCRUM-95)
        diff = [{
            "field_name": "owner",
            "old_value": str(old_owner_id),
            "new_value": str(new_owner_id),
        }]
        record_history_in_transaction(
            conn=db_conn,
            opportunity_id=opportunity_id,
            diffs=diff,
            changed_by=transferred_by,
            changed_at=now,
        )

        db_conn.commit()
    except Exception:
        db_conn.rollback()
        raise

    return list_opportunity_shares(opportunity_id=opportunity_id, conn=db_conn)
