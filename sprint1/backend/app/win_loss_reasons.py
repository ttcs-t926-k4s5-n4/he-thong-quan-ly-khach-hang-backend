"""
app/win_loss_reasons.py — Danh mục Lý do Thắng/Thua & Đối thủ cạnh tranh (S2-10)
Dành cho Giám đốc kinh doanh (Sales Manager)
"""
import re
import time
from typing import Any

from app.db import fetch_all, fetch_one, get_db


def _now_ms() -> int:
    return int(time.time() * 1000)


def sanitize_code(code: str) -> str:
    code = code.strip().lower()
    code = re.sub(r"[^a-z0-9_]", "_", code)
    code = re.sub(r"_+", "_", code).strip("_")
    return code


# ─── 1. Win/Loss Reasons Management ─────────────────────────────────────────

def list_win_loss_reasons(reason_type: str | None = None, is_active_only: bool = False) -> list[dict[str, Any]]:
    conn = get_db()
    sql = "SELECT id, reason_type, reason_code, reason_title, description, is_active, created_at, updated_at FROM dbo.win_loss_reasons WHERE 1=1"
    params: list[Any] = []

    if reason_type in {"win", "loss"}:
        sql += " AND reason_type = ?"
        params.append(reason_type)

    if is_active_only:
        sql += " AND is_active = 1"

    sql += " ORDER BY reason_type ASC, id ASC"
    rows = fetch_all(conn, sql, params)
    for r in rows:
        r["is_active"] = bool(r["is_active"])
    return rows


def get_win_loss_reason(reason_id: int) -> dict[str, Any] | None:
    conn = get_db()
    r = fetch_one(
        conn,
        "SELECT id, reason_type, reason_code, reason_title, description, is_active, created_at, updated_at FROM dbo.win_loss_reasons WHERE id = ?",
        (reason_id,),
    )
    if not r:
        return None
    r["is_active"] = bool(r["is_active"])
    return r


def create_win_loss_reason(
    reason_type: str,
    reason_code: str,
    reason_title: str,
    description: str = "",
    is_active: bool = True,
) -> dict[str, Any]:
    reason_type = reason_type.strip().lower()
    if reason_type not in {"win", "loss"}:
        raise ValueError("reason_type_invalid")

    clean_code = sanitize_code(reason_code)
    if not clean_code:
        raise ValueError("reason_code_invalid")

    reason_title = reason_title.strip()
    if not reason_title:
        raise ValueError("reason_title_empty")

    conn = get_db()
    existing = fetch_one(
        conn,
        "SELECT id FROM dbo.win_loss_reasons WHERE reason_type = ? AND reason_code = ?",
        (reason_type, clean_code),
    )
    if existing:
        raise ValueError("duplicate_reason_code")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.win_loss_reasons (reason_type, reason_code, reason_title, description, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (reason_type, clean_code, reason_title, description.strip(), 1 if is_active else 0, now, now),
    )
    conn.commit()

    new_row = fetch_one(
        conn,
        "SELECT id FROM dbo.win_loss_reasons WHERE reason_type = ? AND reason_code = ?",
        (reason_type, clean_code),
    )
    return get_win_loss_reason(new_row["id"])  # type: ignore


def update_win_loss_reason(
    reason_id: int,
    reason_title: str,
    description: str = "",
    is_active: bool = True,
) -> dict[str, Any]:
    existing = get_win_loss_reason(reason_id)
    if not existing:
        raise LookupError("reason_not_found")

    reason_title = reason_title.strip()
    if not reason_title:
        raise ValueError("reason_title_empty")

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.win_loss_reasons
        SET reason_title = ?, description = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (reason_title, description.strip(), 1 if is_active else 0, now, reason_id),
    )
    conn.commit()
    return get_win_loss_reason(reason_id)  # type: ignore


def delete_win_loss_reason(reason_id: int) -> bool:
    conn = get_db()
    existing = get_win_loss_reason(reason_id)
    if not existing:
        raise LookupError("reason_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.win_loss_reasons WHERE id = ?", (reason_id,))
    conn.commit()
    return True


# ─── 2. Competitors Directory Management ───────────────────────────────────

def list_competitors(is_active_only: bool = False) -> list[dict[str, Any]]:
    conn = get_db()
    sql = "SELECT id, code, name, website, strengths, weaknesses, is_active, created_at, updated_at FROM dbo.competitors WHERE 1=1"
    params: list[Any] = []
    if is_active_only:
        sql += " AND is_active = 1"
    sql += " ORDER BY name ASC, id ASC"
    rows = fetch_all(conn, sql, params)
    for r in rows:
        r["is_active"] = bool(r["is_active"])
    return rows


def get_competitor(competitor_id: int) -> dict[str, Any] | None:
    conn = get_db()
    r = fetch_one(
        conn,
        "SELECT id, code, name, website, strengths, weaknesses, is_active, created_at, updated_at FROM dbo.competitors WHERE id = ?",
        (competitor_id,),
    )
    if not r:
        return None
    r["is_active"] = bool(r["is_active"])
    return r


def create_competitor(
    code: str,
    name: str,
    website: str = "",
    strengths: str = "",
    weaknesses: str = "",
    is_active: bool = True,
) -> dict[str, Any]:
    clean_code = sanitize_code(code)
    if not clean_code:
        raise ValueError("competitor_code_invalid")

    name = name.strip()
    if not name:
        raise ValueError("competitor_name_empty")

    conn = get_db()
    existing = fetch_one(conn, "SELECT id FROM dbo.competitors WHERE code = ?", (clean_code,))
    if existing:
        raise ValueError("duplicate_competitor_code")

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO dbo.competitors (code, name, website, strengths, weaknesses, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (clean_code, name, website.strip(), strengths.strip(), weaknesses.strip(), 1 if is_active else 0, now, now),
    )
    conn.commit()

    new_row = fetch_one(conn, "SELECT id FROM dbo.competitors WHERE code = ?", (clean_code,))
    return get_competitor(new_row["id"])  # type: ignore


def update_competitor(
    competitor_id: int,
    name: str,
    website: str = "",
    strengths: str = "",
    weaknesses: str = "",
    is_active: bool = True,
) -> dict[str, Any]:
    existing = get_competitor(competitor_id)
    if not existing:
        raise LookupError("competitor_not_found")

    name = name.strip()
    if not name:
        raise ValueError("competitor_name_empty")

    conn = get_db()
    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.competitors
        SET name = ?, website = ?, strengths = ?, weaknesses = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, website.strip(), strengths.strip(), weaknesses.strip(), 1 if is_active else 0, now, competitor_id),
    )
    conn.commit()
    return get_competitor(competitor_id)  # type: ignore


def delete_competitor(competitor_id: int) -> bool:
    conn = get_db()
    existing = get_competitor(competitor_id)
    if not existing:
        raise LookupError("competitor_not_found")

    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.competitors WHERE id = ?", (competitor_id,))
    conn.commit()
    return True


# ─── 3. Closing Validation Rule Engine ──────────────────────────────────────

def validate_opportunity_closure(
    conn,
    is_won: bool,
    is_lost: bool,
    win_reason_id: int | None = None,
    loss_reason_id: int | None = None,
    competitor_id: int | None = None,
) -> tuple[bool, str | None]:
    """
    Ràng buộc bắt buộc khi đóng cơ hội (Won/Lost) - S2-10:
    - Khi Chốt Thành công (Won): Bắt buộc chọn Lý do thắng (`win_reason_id`).
    - Khi Chốt Thất bại (Lost): Bắt buộc chọn Lý do thua (`loss_reason_id`) & Đối thủ cạnh tranh (`competitor_id`).
    """
    if is_won:
        if not win_reason_id:
            return False, "Bắt buộc phải chọn Lý do Thắng khi chốt thành công cơ hội kinh doanh."
        try:
            w_id = int(win_reason_id)
        except (ValueError, TypeError):
            return False, "Lý do Thắng được chọn không hợp lệ."
        reason = fetch_one(conn, "SELECT id FROM dbo.win_loss_reasons WHERE id = ? AND reason_type = 'win'", (w_id,))
        if not reason:
            return False, "Lý do Thắng được chọn không hợp lệ."

    elif is_lost:
        if not loss_reason_id:
            return False, "Bắt buộc phải chọn Lý do Thua khi đóng cơ hội thất bại."
        try:
            l_id = int(loss_reason_id)
        except (ValueError, TypeError):
            return False, "Lý do Thua được chọn không hợp lệ."
        reason = fetch_one(conn, "SELECT id FROM dbo.win_loss_reasons WHERE id = ? AND reason_type = 'loss'", (l_id,))
        if not reason:
            return False, "Lý do Thua được chọn không hợp lệ."

        if not competitor_id:
            return False, "Bắt buộc phải chọn Đối thủ cạnh tranh khi chốt thất bại cơ hội."
        try:
            c_id = int(competitor_id)
        except (ValueError, TypeError):
            return False, "Đối thủ cạnh tranh được chọn không hợp lệ."
        comp = fetch_one(conn, "SELECT id FROM dbo.competitors WHERE id = ?", (c_id,))
        if not comp:
            return False, "Đối thủ cạnh tranh được chọn không hợp lệ."

    return True, None
