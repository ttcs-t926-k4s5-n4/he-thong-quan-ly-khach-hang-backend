"""
app/opportunity_filters.py ΓÇö T├¼m kiß║┐m, Lß╗ìc n├óng cao & Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u cho C╞í hß╗Öi kinh doanh (SCRUM-96)

Hß╗ù trß╗ú:
- T├¼m kiß║┐m c╞í hß╗Öi: keyword, stage, min_value, max_value, close_date_from, close_date_to, product_id, owner_id
- Sß║»p xß║┐p an to├án: sort_by (whitelist), sort_order (asc/desc)
- Ph├ón trang: page, page_size (alias per_page)
- Ph├ón quyß╗ün theo vai tr├▓ v├á c╞í hß╗Öi sß╗ƒ hß╗»u / ─æ╞░ß╗úc chia sß║╗ (SCRUM-97)
- CRUD Bß╗Ö lß╗ìc ─æ├ú l╞░u: saved_opportunity_filters (tß║ío, xem danh s├ích, chi tiß║┐t, sß╗¡a, x├│a)
"""
from __future__ import annotations

import json
import time
from typing import Any

from app.custom_fields import batch_get_custom_field_values
from app.db import fetch_all, fetch_one, get_db

ALLOWED_SORT_FIELDS = {
    "id": "o.id",
    "title": "o.title",
    "value": "o.value",
    "stage": "o.stage",
    "expected_close_date": "o.expected_close_date",
    "created_at": "o.created_at",
    "updated_at": "o.updated_at",
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    return "sqlite" in mod or hasattr(conn, "isolation_level")


def ensure_saved_opportunity_filters_table(conn) -> None:
    """Tß╗▒ ─æß╗Öng khß╗ƒi tß║ío bß║úng dbo.saved_opportunity_filters nß║┐u ch╞░a tß╗ôn tß║íi."""
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_opportunity_filters (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                filter_name     TEXT NOT NULL,
                filter_config   TEXT NOT NULL,
                created_at      INTEGER NOT NULL,
                updated_at      INTEGER NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_saved_opp_filters_user_id
            ON saved_opportunity_filters (user_id, created_at DESC);
            """
        )
        # Th├¬m cß╗Öt product_id v├áo opportunities nß║┐u ch╞░a c├│ trong SQLite
        try:
            cur.execute("ALTER TABLE opportunities ADD COLUMN product_id INTEGER;")
        except Exception:
            pass
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'saved_opportunity_filters' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.saved_opportunity_filters (
                id              INT             IDENTITY(1,1) PRIMARY KEY,
                user_id         INT             NOT NULL,
                filter_name     NVARCHAR(255)   NOT NULL,
                filter_config   NVARCHAR(MAX)   NOT NULL,
                created_at      BIGINT          NOT NULL,
                updated_at      BIGINT          NOT NULL,
                CONSTRAINT FK_saved_opp_filters_user FOREIGN KEY (user_id) REFERENCES dbo.users(id) ON DELETE CASCADE
            );
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.saved_opportunity_filters') AND name = N'IX_saved_opp_filters_user_id')
        BEGIN
            CREATE INDEX IX_saved_opp_filters_user_id ON dbo.saved_opportunity_filters (user_id, created_at DESC);
        END
        """
    )
    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.opportunities') AND name = N'product_id')
        BEGIN
            ALTER TABLE dbo.opportunities ADD product_id INT NULL;
        END
        """
    )
    conn.commit()


# ΓöÇΓöÇΓöÇ API T├îM KIß║╛M & Lß╗îC C╞á Hß╗ÿI KINH DOANH (SCRUM-96) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def search_and_filter_opportunities(
    user: Any,
    keyword: str = "",
    stage: str = "",
    min_value: float | None = None,
    max_value: float | None = None,
    close_date_from: str = "",
    close_date_to: str = "",
    product_id: int | None = None,
    owner_id: int | None = None,
    cf_filters: dict[str, Any] | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    conn: Any = None,
) -> dict[str, Any]:
    """
    T├¼m kiß║┐m v├á lß╗ìc c╞í hß╗Öi kinh doanh ─æa ti├¬u ch├¡, ph├ón trang v├á sß║»p xß║┐p an to├án.
    """
    # 1. Validation khoß║úng gi├í trß╗ï
    if min_value is not None and max_value is not None:
        if min_value > max_value:
            raise ValueError({"message": "Gi├í trß╗ï tß╗æi thiß╗âu kh├┤ng ─æ╞░ß╗úc lß╗¢n h╞ín gi├í trß╗ï tß╗æi ─æa."})

    # 2. Validation khoß║úng ng├áy chß╗æt
    date_from = close_date_from.strip()
    date_to = close_date_to.strip()
    if date_from and date_to:
        if date_from > date_to:
            raise ValueError({"message": "Ng├áy bß║»t ─æß║ºu kh├┤ng ─æ╞░ß╗úc sau ng├áy kß║┐t th├║c."})

    db_conn = conn or get_db()
    ensure_saved_opportunity_filters_table(db_conn)

    where_clauses = ["1=1"]
    params: list[Any] = []

    # 3. Keyword: T├¼m theo t├¬n c╞í hß╗Öi, m├ú c╞í hß╗Öi (ID) hoß║╖c t├¬n kh├ích h├áng
    clean_kw = keyword.strip()
    if clean_kw:
        if clean_kw.isdigit():
            where_clauses.append("(o.title LIKE ? OR c.name LIKE ? OR o.id = ?)")
            kw_param = f"%{clean_kw}%"
            params.extend([kw_param, kw_param, int(clean_kw)])
        else:
            where_clauses.append("(o.title LIKE ? OR c.name LIKE ?)")
            kw_param = f"%{clean_kw}%"
            params.extend([kw_param, kw_param])

    # 4. Giai ─æoß║ín kinh doanh (stage hoß║╖c stage_key)
    clean_stage = stage.strip()
    if clean_stage:
        where_clauses.append("(o.stage = ? OR o.stage_key = ?)")
        params.extend([clean_stage, clean_stage])

    # 5. Khoß║úng gi├í trß╗ï (min_value, max_value)
    if min_value is not None:
        where_clauses.append("o.value >= ?")
        params.append(float(min_value))
    if max_value is not None:
        where_clauses.append("o.value <= ?")
        params.append(float(max_value))

    # 6. Khoß║úng ng├áy chß╗æt dß╗▒ kiß║┐n
    if date_from:
        where_clauses.append("o.expected_close_date >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("o.expected_close_date <= ?")
        params.append(date_to)

    # 7. Sß║ún phß║⌐m li├¬n quan
    if product_id is not None and int(product_id) > 0:
        where_clauses.append("o.product_id = ?")
        params.append(int(product_id))

    # 8. Ng╞░ß╗¥i sß╗ƒ hß╗»u
    if owner_id is not None and int(owner_id) > 0:
        where_clauses.append("COALESCE(o.owner_id, o.created_by) = ?")
        params.append(int(owner_id))

    # 9. Ph├ón quyß╗ün dß╗» liß╗çu (RBAC Data Scope)
    # Admin v├á Manager xem ─æ╞░ß╗úc to├án bß╗Ö.
    # Employee chß╗ë xem c╞í hß╗Öi do m├¼nh sß╗ƒ hß╗»u HOß║╢C ─æ╞░ß╗úc chia sß║╗ qua opportunity_shares (SCRUM-97)
    user_role = getattr(user, "role", "")
    user_id = getattr(user, "id", None)
    if user_role not in {"admin", "manager"} and user_id is not None:
        shares_table = "dbo.opportunity_shares" if not _is_sqlite(db_conn) else "opportunity_shares"
        where_clauses.append(
            f"""
            (
                COALESCE(o.owner_id, o.created_by) = ?
                OR EXISTS (
                    SELECT 1 FROM {shares_table} os
                    WHERE os.opportunity_id = o.id AND os.user_id = ?
                )
            )
            """
        )
        params.extend([int(user_id), int(user_id)])

    # 10. Lß╗ìc theo tr╞░ß╗¥ng t├╣y chß╗ënh
    if cf_filters:
        cf_table = "dbo.custom_field_values" if not _is_sqlite(db_conn) else "custom_field_values"
        cf_def = "dbo.custom_field_definitions" if not _is_sqlite(db_conn) else "custom_field_definitions"
        for key, val in cf_filters.items():
            if val is not None and str(val).strip() != "":
                where_clauses.append(
                    f"""
                    EXISTS (
                        SELECT 1 FROM {cf_table} cfv_f
                        INNER JOIN {cf_def} cfd_f ON cfv_f.field_id = cfd_f.id
                        WHERE cfv_f.entity_type = 'opportunity'
                          AND cfv_f.entity_id = o.id
                          AND cfd_f.field_key = ?
                          AND cfv_f.field_value LIKE ?
                    )
                    """
                )
                params.extend([key, f"%{str(val).strip()}%"])

    where_sql = " AND ".join(where_clauses)

    opp_table = "dbo.opportunities" if not _is_sqlite(db_conn) else "opportunities"
    cust_table = "dbo.customers" if not _is_sqlite(db_conn) else "customers"
    users_table = "dbo.users" if not _is_sqlite(db_conn) else "users"

    # ─Éß║┐m tß╗òng sß╗æ kß║┐t quß║ú
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM {opp_table} o
        LEFT JOIN {cust_table} c ON o.customer_id = c.id
        WHERE {where_sql}
    """
    count_row = fetch_one(db_conn, count_sql, params)
    total = count_row["total"] if count_row else 0

    # Xß╗¡ l├╜ sß║»p xß║┐p an to├án
    sort_key = sort_by.strip().lower()
    sort_column = ALLOWED_SORT_FIELDS.get(sort_key, "o.created_at")
    direction = "ASC" if sort_order.strip().lower() == "asc" else "DESC"

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    if _is_sqlite(db_conn):
        select_sql = f"""
            SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.stage_key,
                   o.win_probability, o.expected_close_date, o.meetings_count,
                   o.product_id,
                   o.closed_at, o.created_by, u.full_name AS creator_name,
                   COALESCE(o.owner_id, o.created_by) AS owner_id,
                   COALESCE(ow.full_name, u.full_name) AS owner_name,
                   o.created_at, o.updated_at
            FROM {opp_table} o
            LEFT JOIN {cust_table} c ON o.customer_id = c.id
            LEFT JOIN {users_table} u ON o.created_by = u.id
            LEFT JOIN {users_table} ow ON o.owner_id = ow.id
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, o.id DESC
            LIMIT ? OFFSET ?
        """
        query_params = params + [page_size, offset]
    else:
        select_sql = f"""
            SELECT o.id, o.title, o.customer_id, c.name AS customer_name, o.value, o.stage, o.stage_key,
                   o.win_probability, o.expected_close_date, o.meetings_count,
                   o.product_id,
                   o.closed_at, o.created_by, u.full_name AS creator_name,
                   COALESCE(o.owner_id, o.created_by) AS owner_id,
                   COALESCE(ow.full_name, u.full_name) AS owner_name,
                   o.created_at, o.updated_at
            FROM {opp_table} o
            LEFT JOIN {cust_table} c ON o.customer_id = c.id
            LEFT JOIN {users_table} u ON o.created_by = u.id
            LEFT JOIN {users_table} ow ON o.owner_id = ow.id
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, o.id DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        query_params = params + [offset, page_size]

    items = fetch_all(db_conn, select_sql, query_params)

    for item in items:
        val = float(item.get("value") or 0.0)
        item["value"] = val
        prob = item.get("win_probability") or 0
        item["win_probability"] = prob
        item["forecast_amount"] = val * (prob / 100.0)

    entity_ids = [item["id"] for item in items]
    cf_map = batch_get_custom_field_values(db_conn, "opportunity", entity_ids)

    for item in items:
        item["custom_fields"] = cf_map.get(item["id"], {})

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "sort_by": sort_key if sort_key in ALLOWED_SORT_FIELDS else "created_at",
        "sort_order": direction.lower(),
    }


# ΓöÇΓöÇΓöÇ API Bß╗ÿ Lß╗îC ─É├â L╞»U (SAVED OPPORTUNITY FILTERS) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_saved_opportunity_filter(
    user_id: int,
    filter_name: str,
    filter_config: dict[str, Any] | str,
    conn: Any = None,
) -> dict[str, Any]:
    name = (filter_name or "").strip()
    if not name:
        raise ValueError({"message": "T├¬n bß╗Ö lß╗ìc kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng."})

    if isinstance(filter_config, dict):
        # Loß║íi bß╗Å c├íc th├┤ng tin nhß║íy cß║úm nß║┐u c├│
        clean_config = {k: v for k, v in filter_config.items() if k not in {"token", "password", "secret"}}
        config_str = json.dumps(clean_config, ensure_ascii=False)
    elif isinstance(filter_config, str):
        try:
            parsed = json.loads(filter_config)
            clean_config = {k: v for k, v in parsed.items() if k not in {"token", "password", "secret"}}
            config_str = json.dumps(clean_config, ensure_ascii=False)
        except Exception:
            raise ValueError({"message": "Cß║Ñu h├¼nh bß╗Ö lß╗ìc phß║úi l├á JSON hß╗úp lß╗ç."})
    else:
        raise ValueError({"message": "Cß║Ñu h├¼nh bß╗Ö lß╗ìc kh├┤ng hß╗úp lß╗ç."})

    db_conn = conn or get_db()
    ensure_saved_opportunity_filters_table(db_conn)

    now = _now_ms()
    cur = db_conn.cursor()
    table_name = "dbo.saved_opportunity_filters" if not _is_sqlite(db_conn) else "saved_opportunity_filters"

    cur.execute(
        f"""
        INSERT INTO {table_name} (user_id, filter_name, filter_config, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, name, config_str, now, now),
    )
    db_conn.commit()

    new_row = fetch_one(
        db_conn,
        f"SELECT MAX(id) AS id FROM {table_name} WHERE user_id = ? AND filter_name = ?",
        (user_id, name),
    )
    filter_id = new_row["id"]
    return get_saved_opportunity_filter(filter_id=filter_id, user_id=user_id, conn=db_conn)


def list_saved_opportunity_filters(user_id: int, conn: Any = None) -> list[dict[str, Any]]:
    db_conn = conn or get_db()
    ensure_saved_opportunity_filters_table(db_conn)

    table_name = "dbo.saved_opportunity_filters" if not _is_sqlite(db_conn) else "saved_opportunity_filters"
    rows = fetch_all(
        db_conn,
        f"""
        SELECT id, user_id, filter_name, filter_config, created_at, updated_at
        FROM {table_name}
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    for r in rows:
        try:
            r["filter_config"] = json.loads(r.get("filter_config") or "{}")
        except Exception:
            r["filter_config"] = {}
    return rows


def get_saved_opportunity_filter(filter_id: int, user_id: int, conn: Any = None) -> dict[str, Any]:
    db_conn = conn or get_db()
    ensure_saved_opportunity_filters_table(db_conn)

    table_name = "dbo.saved_opportunity_filters" if not _is_sqlite(db_conn) else "saved_opportunity_filters"
    row = fetch_one(
        db_conn,
        f"""
        SELECT id, user_id, filter_name, filter_config, created_at, updated_at
        FROM {table_name}
        WHERE id = ?
        """,
        (filter_id,),
    )
    if not row:
        raise LookupError("filter_not_found")

    if row["user_id"] != user_id:
        raise PermissionError("filter_forbidden")

    try:
        row["filter_config"] = json.loads(row.get("filter_config") or "{}")
    except Exception:
        row["filter_config"] = {}

    return row


def update_saved_opportunity_filter(
    filter_id: int,
    user_id: int,
    filter_name: str,
    filter_config: dict[str, Any] | str,
    conn: Any = None,
) -> dict[str, Any]:
    # Kiß╗âm tra tß╗ôn tß║íi v├á quyß╗ün sß╗ƒ hß╗»u
    get_saved_opportunity_filter(filter_id=filter_id, user_id=user_id, conn=conn)

    name = (filter_name or "").strip()
    if not name:
        raise ValueError({"message": "T├¬n bß╗Ö lß╗ìc kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng."})

    if isinstance(filter_config, dict):
        clean_config = {k: v for k, v in filter_config.items() if k not in {"token", "password", "secret"}}
        config_str = json.dumps(clean_config, ensure_ascii=False)
    elif isinstance(filter_config, str):
        try:
            parsed = json.loads(filter_config)
            clean_config = {k: v for k, v in parsed.items() if k not in {"token", "password", "secret"}}
            config_str = json.dumps(clean_config, ensure_ascii=False)
        except Exception:
            raise ValueError({"message": "Cß║Ñu h├¼nh bß╗Ö lß╗ìc phß║úi l├á JSON hß╗úp lß╗ç."})
    else:
        raise ValueError({"message": "Cß║Ñu h├¼nh bß╗Ö lß╗ìc kh├┤ng hß╗úp lß╗ç."})

    db_conn = conn or get_db()
    table_name = "dbo.saved_opportunity_filters" if not _is_sqlite(db_conn) else "saved_opportunity_filters"
    now = _now_ms()

    cur = db_conn.cursor()
    cur.execute(
        f"""
        UPDATE {table_name}
        SET filter_name = ?, filter_config = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, config_str, now, filter_id, user_id),
    )
    db_conn.commit()
    return get_saved_opportunity_filter(filter_id=filter_id, user_id=user_id, conn=db_conn)


def delete_saved_opportunity_filter(filter_id: int, user_id: int, conn: Any = None) -> bool:
    # Kiß╗âm tra quyß╗ün sß╗ƒ hß╗»u tr╞░ß╗¢c khi x├│a
    get_saved_opportunity_filter(filter_id=filter_id, user_id=user_id, conn=conn)

    db_conn = conn or get_db()
    table_name = "dbo.saved_opportunity_filters" if not _is_sqlite(db_conn) else "saved_opportunity_filters"

    cur = db_conn.cursor()
    cur.execute(f"DELETE FROM {table_name} WHERE id = ? AND user_id = ?", (filter_id, user_id))
    db_conn.commit()
    return True
