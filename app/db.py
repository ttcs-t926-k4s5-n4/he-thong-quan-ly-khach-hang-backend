"""Kết nối CSDL SQLite và các hàm truy vấn tiện ích."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g

from app.labels import search_text

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"], timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        # Hàm tìm kiếm không phân biệt hoa thường và dấu tiếng Việt
        conn.create_function("search_text", 1, search_text, deterministic=True)
        g.db = conn
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)


def init_db() -> None:
    """Tạo các bảng nếu chưa có (an toàn khi chạy nhiều lần) và tự động nâng cấp cấu trúc CSDL."""
    get_db().executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    migrate_db()


def migrate_db(conn: sqlite3.Connection | None = None) -> None:
    """Nâng cấp cấu trúc CSDL cho database đã có từ trước mà không làm mất hoặc reset dữ liệu.
    
    Tự động bổ sung các cột và bảng mới (failed_login_attempts, locked_until, revoked_tokens)
    khi chạy trên bản sao CSDL cũ.
    """
    db_conn = conn if conn is not None else get_db()
    cursor = db_conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'")
    if cursor.fetchone():
        user_cols = {r[1] for r in db_conn.execute("PRAGMA table_info(users)").fetchall()}
        if "failed_login_attempts" not in user_cols:
            db_conn.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0")
        if "locked_until" not in user_cols:
            db_conn.execute("ALTER TABLE users ADD COLUMN locked_until TEXT")

    db_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            token_hash  TEXT PRIMARY KEY,
            revoked_at  TEXT NOT NULL
        )
        """
    )
    db_conn.commit()


def drop_all() -> None:
    """Xoá toàn bộ bảng (dùng khi tạo lại dữ liệu mẫu)."""
    conn = get_db()
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    for name in names:
        conn.execute(f'DROP TABLE IF EXISTS "{name}"')
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")


def rows(sql: str, params=()) -> list[dict]:
    return [dict(r) for r in get_db().execute(sql, tuple(params)).fetchall()]


def row(sql: str, params=()) -> dict | None:
    result = get_db().execute(sql, tuple(params)).fetchone()
    return dict(result) if result else None


def scalar(sql: str, params=()):
    result = get_db().execute(sql, tuple(params)).fetchone()
    return result[0] if result else None


def execute(sql: str, params=()) -> int:
    return get_db().execute(sql, tuple(params)).lastrowid


def commit() -> None:
    get_db().commit()


def rollback_quietly() -> None:
    conn = g.get("db")
    if conn is not None:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass


if __name__ == "__main__":
    from app import create_app

    _app = create_app()
    with _app.app_context():
        init_db()
        print("Đã khởi tạo và nâng cấp CSDL thành công (bảo toàn toàn bộ dữ liệu có sẵn).")

