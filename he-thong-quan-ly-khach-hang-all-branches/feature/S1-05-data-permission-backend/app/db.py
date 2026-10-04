"""Kết nối SQLite, tạo bảng và dữ liệu mẫu."""
import sqlite3

import click
from flask import current_app, g

SCHEMA = """
DROP TABLE IF EXISTS quotes;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS opportunities;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE users (
    id        INTEGER PRIMARY KEY,
    username  TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role      TEXT NOT NULL CHECK (role IN ('NHAN_VIEN', 'TRUONG_NHOM', 'GIAM_DOC')),
    team_id   INTEGER REFERENCES teams(id)
);

CREATE TABLE customers (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL,
    phone    TEXT,
    email    TEXT,
    address  TEXT,
    owner_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE opportunities (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    value       INTEGER NOT NULL DEFAULT 0,
    stage       TEXT NOT NULL,
    owner_id    INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE activities (
    id            INTEGER PRIMARY KEY,
    subject       TEXT NOT NULL,
    customer_id   INTEGER NOT NULL REFERENCES customers(id),
    type          TEXT NOT NULL,
    activity_date TEXT NOT NULL,
    owner_id      INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE quotes (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    amount      INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL,
    owner_id    INTEGER NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_customers_owner     ON customers(owner_id);
CREATE INDEX idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX idx_activities_owner    ON activities(owner_id);
CREATE INDEX idx_quotes_owner        ON quotes(owner_id);
CREATE INDEX idx_users_team          ON users(team_id);
"""

TEAMS = [(1, "Nhóm Miền Bắc"), (2, "Nhóm Miền Nam")]

USERS = [
    (1, "giamdoc",        "Trần Văn Giám",  "GIAM_DOC",    None),
    (2, "truongnhom_bac", "Lê Thị Hoa",     "TRUONG_NHOM", 1),
    (3, "nhanvien_a",     "Nguyễn Văn An",  "NHAN_VIEN",   1),
    (4, "nhanvien_b",     "Phạm Thị Bình",  "NHAN_VIEN",   1),
    (5, "truongnhom_nam", "Hoàng Văn Nam",  "TRUONG_NHOM", 2),
    (6, "nhanvien_c",     "Đỗ Minh Châu",   "NHAN_VIEN",   2),
]

# (id, tên, điện thoại, email, địa chỉ, owner_id)
CUSTOMERS = [
    (1, "Công ty TNHH Minh Phát",  "0912000001", "lienhe@minhphat.vn",  "Hà Nội",      3),
    (2, "Công ty CP Sao Việt",     "0912000002", "info@saoviet.vn",     "Bắc Ninh",    3),
    (3, "Công ty TNHH Hòa Bình",   "0912000003", "kd@hoabinh.vn",       "Thái Nguyên", 4),
    (4, "Cửa hàng Bình An",        "0912000004", "binhan@gmail.com",    "Hải Phòng",   4),
    (5, "Công ty CP Phương Nam",   "0912000005", "sales@phuongnam.vn",  "TP.HCM",      6),
    (6, "Tập đoàn Đại Dương",      "0912000006", "contact@daiduong.vn", "Hà Nội",      2),
    (7, "Công ty TNHH Mekong",     "0912000007", "hello@mekong.vn",     "Cần Thơ",     5),
    (8, "Công ty CP Toàn Cầu",     "0912000008", "global@toancau.vn",   "Đà Nẵng",     1),
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(seed: bool = True):
    db = get_db()
    db.executescript(SCHEMA)
    if seed:
        seed_db(db)
    db.commit()


def seed_db(db: sqlite3.Connection):
    db.executemany("INSERT INTO teams VALUES (?, ?)", TEAMS)
    db.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", USERS)
    db.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", CUSTOMERS)
    stages = ["Tiếp cận", "Đàm phán", "Chốt đơn"]
    statuses = ["Nháp", "Đã gửi", "Đã duyệt"]
    for cid, name, *_rest, owner in CUSTOMERS:
        db.execute("INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?)",
                   (cid, f"Cơ hội bán hàng - {name}", cid, cid * 50_000_000,
                    stages[cid % 3], owner))
        db.execute("INSERT INTO activities VALUES (?, ?, ?, ?, ?, ?)",
                   (cid, f"Gọi điện chăm sóc {name}", cid, "Cuộc gọi",
                    f"2026-09-{cid:02d}", owner))
        db.execute("INSERT INTO quotes VALUES (?, ?, ?, ?, ?, ?)",
                   (cid, f"BG-2026-{cid:04d}", cid, cid * 20_000_000,
                    statuses[cid % 3], owner))


@click.command("init-db")
def init_db_command():
    """Tạo lại CSDL và nạp dữ liệu mẫu."""
    init_db()
    click.echo("Đã khởi tạo cơ sở dữ liệu và dữ liệu mẫu.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
