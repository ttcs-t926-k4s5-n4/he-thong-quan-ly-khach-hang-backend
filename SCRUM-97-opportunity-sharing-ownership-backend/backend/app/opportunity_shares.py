"""
app/opportunity_shares.py ΓÇö Quß║ún l├╜ Chia sß║╗ & Chuyß╗ân quyß╗ün Sß╗ƒ hß╗»u C╞í hß╗Öi kinh doanh (SCRUM-97)

Mß╗Ñc ti├¬u:
- Duy tr├¼ mß╗Öt Primary Owner (ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh chß╗ïu tr├ích nhiß╗çm)
- Hß╗ù trß╗ú nhiß╗üu Shared Members vß╗¢i c├íc cß║Ñp ─æß╗Ö quyß╗ün: 'read', 'edit', 'manage'
- Cho ph├⌐p Primary Owner / Manager / Admin chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh
- T├¡ch hß╗úp ghi nhß║¡n lß╗ïch sß╗¡ thay ─æß╗òi v├áo dbo.opportunity_history (SCRUM-95)
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
    """Tß╗▒ ─æß╗Öng khß╗ƒi tß║ío bß║úng dbo.opportunity_shares nß║┐u ch╞░a tß╗ôn tß║íi."""
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
    """Lß║Ñy bß║ún ghi chia sß║╗ cß╗ºa mß╗Öt user ─æß╗æi vß╗¢i c╞í hß╗Öi."""
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
    Kiß╗âm tra quyß╗ün truy cß║¡p chi tiß║┐t cß╗ºa ng╞░ß╗¥i d├╣ng ─æß╗æi vß╗¢i c╞í hß╗Öi (SCRUM-97):
    - required_permission: 'read', 'edit', 'share', 'transfer'
    Trß║ú vß╗ü (is_allowed, error_message).
    """
    if not user:
        return False, "Ch╞░a ─æ─âng nhß║¡p."

    role = getattr(user, "role", "")
    if role in {"admin", "manager"}:
        return True, ""

    user_id = getattr(user, "id", None)
    if user_id is None:
        return False, "Kh├┤ng x├íc ─æß╗ïnh danh t├¡nh ng╞░ß╗¥i d├╣ng."

    primary_owner_id = opportunity.get("owner_id")
    if primary_owner_id is None:
        primary_owner_id = opportunity.get("created_by")

    is_primary_owner = (primary_owner_id is not None and int(primary_owner_id) == int(user_id))
    if is_primary_owner:
        # Primary Owner c├│ to├án quyß╗ün: xem, sß╗¡a, chia sß║╗ v├á chuyß╗ân quyß╗ün sß╗ƒ hß╗»u
        return True, ""

    # Nß║┐u y├¬u cß║ºu 'transfer' (chuyß╗ân quyß╗ün sß╗ƒ hß╗»u) th├¼ chß╗ë Primary Owner, Manager, Admin mß╗¢i ─æ╞░ß╗úc
    if required_permission == "transfer":
        return False, "Chß╗ë Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh hoß║╖c Quß║ún trß╗ï vi├¬n/Tr╞░ß╗ƒng nh├│m mß╗¢i c├│ quyß╗ün chuyß╗ân quyß╗ün sß╗ƒ hß╗»u."

    # Kiß╗âm tra quyß╗ün qua bß║ún ghi chia sß║╗ (Shared Member)
    share = get_user_share_record(opportunity_id=opportunity["id"], user_id=user_id, conn=conn)
    if not share:
        return False, "Bß║ín kh├┤ng c├│ quyß╗ün truy cß║¡p c╞í hß╗Öi n├áy."

    perm = (share.get("permission_level") or "read").lower()

    if required_permission == "read":
        return True, ""
    elif required_permission in {"edit", "activity"}:
        if perm in {"edit", "manage"}:
            return True, ""
        return False, "Bß║ín chß╗ë c├│ quyß╗ün xem, kh├┤ng c├│ quyß╗ün chß╗ënh sß╗¡a hoß║╖c ghi nhß║¡n hoß║ít ─æß╗Öng."
    elif required_permission == "share":
        if perm == "manage":
            return True, ""
        return False, "Bß║ín kh├┤ng c├│ quyß╗ün quß║ún l├╜ chia sß║╗ c╞í hß╗Öi n├áy."

    return False, "Y├¬u cß║ºu quyß╗ün kh├┤ng hß╗úp lß╗ç."


def list_opportunity_shares(opportunity_id: int, conn: Any = None) -> dict[str, Any]:
    """Lß║Ñy th├┤ng tin ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh v├á danh s├ích th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"
    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"

    # Lß║Ñy th├┤ng tin c╞í hß╗Öi v├á ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh
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

    # Lß║Ñy danh s├ích th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗
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
    """Chia sß║╗ c╞í hß╗Öi cho mß╗Öt th├ánh vi├¬n mß╗¢i."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    clean_perm = (permission_level or "read").strip().lower()
    if clean_perm not in VALID_PERMISSION_LEVELS:
        raise ValueError({"message": f"Quyß╗ün chia sß║╗ kh├┤ng hß╗úp lß╗ç. Phß║úi l├á mß╗Öt trong: {', '.join(VALID_PERMISSION_LEVELS)}"})

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"
    shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"

    # Kiß╗âm tra c╞í hß╗Öi tß╗ôn tß║íi
    opp = fetch_one(db_conn, f"SELECT id, COALESCE(owner_id, created_by) AS owner_id FROM {opp_table} WHERE id = ?", (opportunity_id,))
    if not opp:
        raise LookupError("opportunity_not_found")

    # Kiß╗âm tra th├ánh vi├¬n mß╗Ñc ti├¬u tß╗ôn tß║íi v├á ─æang hoß║ít ─æß╗Öng
    target_user = fetch_one(db_conn, f"SELECT id, full_name, email, is_active FROM {users_table} WHERE id = ?", (user_id,))
    if not target_user:
        raise ValueError({"message": "Th├ánh vi├¬n cß║ºn chia sß║╗ kh├┤ng tß╗ôn tß║íi trong hß╗ç thß╗æng."})
    if not target_user.get("is_active", True):
        raise ValueError({"message": "T├ái khoß║ún cß╗ºa th├ánh vi├¬n n├áy ─æang bß╗ï v├┤ hiß╗çu h├│a."})

    # Kh├┤ng cho ph├⌐p chia sß║╗ vß╗¢i ch├¡nh Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh
    if int(opp["owner_id"]) == int(user_id):
        raise ValueError({"message": "Kh├┤ng thß╗â chia sß║╗ c╞í hß╗Öi cho Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh."})

    # Kiß╗âm tra kh├┤ng th├¬m tr├╣ng th├ánh vi├¬n
    existing_share = fetch_one(db_conn, f"SELECT id FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?", (opportunity_id, user_id))
    if existing_share:
        raise ValueError({"message": "Th├ánh vi├¬n n├áy ─æ├ú ─æ╞░ß╗úc chia sß║╗ c╞í hß╗Öi."})

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
    """Cß║¡p nhß║¡t quyß╗ün chia sß║╗ cß╗ºa mß╗Öt th├ánh vi├¬n."""
    db_conn = conn or get_db()
    ensure_opportunity_shares_table(db_conn)

    clean_perm = (permission_level or "").strip().lower()
    if clean_perm not in VALID_PERMISSION_LEVELS:
        raise ValueError({"message": f"Quyß╗ün chia sß║╗ kh├┤ng hß╗úp lß╗ç. Phß║úi l├á mß╗Öt trong: {', '.join(VALID_PERMISSION_LEVELS)}"})

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
    """Gß╗í quyß╗ün chia sß║╗ cß╗ºa mß╗Öt th├ánh vi├¬n."""
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
    Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh cß╗ºa c╞í hß╗Öi (SCRUM-97):
    - Cß║¡p nhß║¡t owner_id trong dbo.opportunities
    - X├│a new_owner_id khß╗Åi dbo.opportunity_shares (nß║┐u tr╞░ß╗¢c ─æ├│ ─æ╞░ß╗úc chia sß║╗)
    - Tß╗▒ ─æß╗Öng th├¬m old_owner_id v├áo dbo.opportunity_shares vß╗¢i quyß╗ün 'edit' ─æß╗â vß║½n theo d├╡i ─æ╞░ß╗úc
    - Ghi nhß║¡n lß╗ïch sß╗¡ chuyß╗ân quyß╗ün sß╗ƒ hß╗»u v├áo dbo.opportunity_history (SCRUM-95)
    - To├án bß╗Ö chß║íy trong c├╣ng 1 transaction nguy├¬n tß╗¡
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
        raise ValueError({"message": "Ng╞░ß╗¥i d├╣ng n├áy hiß╗çn ─æ├ú l├á Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh cß╗ºa c╞í hß╗Öi."})

    new_owner = fetch_one(db_conn, f"SELECT id, full_name, is_active FROM {users_table} WHERE id = ?", (new_owner_id,))
    if not new_owner:
        raise ValueError({"message": "Chß╗º sß╗ƒ hß╗»u mß╗¢i kh├┤ng tß╗ôn tß║íi trong hß╗ç thß╗æng."})
    if not new_owner.get("is_active", True):
        raise ValueError({"message": "T├ái khoß║ún cß╗ºa chß╗º sß╗ƒ hß╗»u mß╗¢i ─æang bß╗ï v├┤ hiß╗çu h├│a."})

    now = _now_ms()
    cur = db_conn.cursor()
    try:
        # 1. Cß║¡p nhß║¡t chß╗º sß╗ƒ hß╗»u mß╗¢i trong bß║úng opportunities
        cur.execute(
            f"UPDATE {opp_table} SET owner_id = ?, updated_at = ? WHERE id = ?",
            (new_owner_id, now, opportunity_id),
        )

        # 2. X├│a new_owner_id khß╗Åi bß║úng shares nß║┐u tr╞░ß╗¢c ─æ├│ l├á shared member
        cur.execute(
            f"DELETE FROM {shares_table} WHERE opportunity_id = ? AND user_id = ?",
            (opportunity_id, new_owner_id),
        )

        # 3. Th├¬m old_owner_id v├áo bß║úng shares vß╗¢i quyß╗ün 'edit' ─æß╗â giß╗» quyß╗ün theo d├╡i
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

        # 4. Ghi lß╗ïch sß╗¡ chuyß╗ân quyß╗ün sß╗ƒ hß╗»u v├áo dbo.opportunity_history (SCRUM-95)
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
