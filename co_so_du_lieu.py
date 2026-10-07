# -*- coding: utf-8 -*-
"""
CƠ SỞ DỮ LIỆU (SQLite)
Tạo bảng cho cả 3 chức năng, chỉ mục tăng tốc trang 360 và dữ liệu mẫu.
"""
import os
import sqlite3
from datetime import datetime

from flask import g

from cau_hinh import TEP_CSDL, THU_MUC_TEP_DINH_KEM


def bay_gio() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ket_noi_csdl():
    """Lấy kết nối SQLite dùng chung trong một request."""
    if "db" not in g:
        g.db = sqlite3.connect(TEP_CSDL)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def dong_csdl(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ghi_hoat_dong(db, khach_hang_id, loai, noi_dung, nguoi_thuc_hien_id=None):
    """Ghi một dòng vào dòng thời gian hoạt động của khách hàng (SCRUM-71)."""
    db.execute(
        """INSERT INTO hoat_dong (khach_hang_id, loai, noi_dung, nguoi_thuc_hien_id, thoi_gian)
           VALUES (?, ?, ?, ?, ?)""",
        (khach_hang_id, loai, noi_dung, nguoi_thuc_hien_id, bay_gio()),
    )


def khoi_tao_csdl():
    """Tạo toàn bộ bảng, chỉ mục và dữ liệu người dùng mẫu."""
    os.makedirs(THU_MUC_TEP_DINH_KEM, exist_ok=True)
    db = sqlite3.connect(TEP_CSDL)
    db.executescript(
        """
        -- Người dùng hệ thống (phục vụ phân quyền SCRUM-69)
        CREATE TABLE IF NOT EXISTS nguoi_dung (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten    TEXT NOT NULL,
            vai_tro   TEXT NOT NULL,          -- Quản trị hệ thống / Trưởng nhóm / Nhân viên kinh doanh
            nhom      TEXT                    -- ví dụ: Nhóm kinh doanh 1
        );

        -- [SCRUM-69] Hồ sơ khách hàng doanh nghiệp
        CREATE TABLE IF NOT EXISTS khach_hang (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_cong_ty    TEXT NOT NULL,
            ma_so_thue     TEXT,              -- nếu có thì phải duy nhất (kiểm tra ở API)
            nganh_nghe     TEXT,
            quy_mo         TEXT,
            website        TEXT,
            dia_chi        TEXT,
            nguoi_so_huu_id INTEGER NOT NULL REFERENCES nguoi_dung(id),
            trang_thai     TEXT NOT NULL,     -- Tiềm năng / Đang giao dịch / Khách hàng / Ngừng hợp tác
            ngay_tao       TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS chi_muc_mst_duy_nhat
            ON khach_hang(ma_so_thue) WHERE ma_so_thue IS NOT NULL AND ma_so_thue <> '';

        -- [SCRUM-70] Người liên hệ của khách hàng
        CREATE TABLE IF NOT EXISTS nguoi_lien_he (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id   INTEGER NOT NULL REFERENCES khach_hang(id),
            ho_ten          TEXT NOT NULL,
            chuc_danh       TEXT,
            email           TEXT,
            so_dien_thoai   TEXT,
            vai_tro_mua     TEXT,             -- Người quyết định / ảnh hưởng / dùng cuối / cản trở
            la_dau_moi_chinh INTEGER NOT NULL DEFAULT 0,  -- 1 = đầu mối chính
            ngay_tao        TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS chi_muc_nlh_khach_hang ON nguoi_lien_he(khach_hang_id);

        -- [SCRUM-70] Lịch sử công ty của người liên hệ (giữ nguyên khi chuyển công ty)
        CREATE TABLE IF NOT EXISTS lich_su_nguoi_lien_he (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nguoi_lien_he_id INTEGER NOT NULL REFERENCES nguoi_lien_he(id),
            khach_hang_id    INTEGER NOT NULL REFERENCES khach_hang(id),
            ten_cong_ty      TEXT NOT NULL,   -- lưu lại tên tại thời điểm đó
            tu_ngay          TEXT NOT NULL,
            den_ngay         TEXT              -- NULL = đang thuộc công ty này
        );
        CREATE INDEX IF NOT EXISTS chi_muc_ls_nlh ON lich_su_nguoi_lien_he(nguoi_lien_he_id);

        -- Cơ hội bán hàng (phục vụ trang 360: tổng giá trị đã ký / đang mở)
        CREATE TABLE IF NOT EXISTS co_hoi (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL REFERENCES khach_hang(id),
            ten_co_hoi    TEXT NOT NULL,
            gia_tri       REAL NOT NULL DEFAULT 0,   -- đơn vị: VNĐ
            trang_thai    TEXT NOT NULL,             -- Đang mở / Đã thắng / Đã thua
            ngay_tao      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS chi_muc_co_hoi_kh ON co_hoi(khach_hang_id);

        -- [SCRUM-71] Dòng thời gian hoạt động
        CREATE TABLE IF NOT EXISTS hoat_dong (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id     INTEGER NOT NULL REFERENCES khach_hang(id),
            loai              TEXT NOT NULL,   -- ví dụ: Ghi chú, Cuộc gọi, Email, Cuộc họp, Hệ thống
            noi_dung          TEXT NOT NULL,
            nguoi_thuc_hien_id INTEGER REFERENCES nguoi_dung(id),
            thoi_gian         TEXT NOT NULL
        );
        -- Chỉ mục kép giúp trang 360 tải 500 hoạt động dưới 1,5 giây
        CREATE INDEX IF NOT EXISTS chi_muc_hoat_dong_kh_tg
            ON hoat_dong(khach_hang_id, thoi_gian DESC);

        -- [SCRUM-71] Tệp đính kèm của khách hàng
        CREATE TABLE IF NOT EXISTS tep_dinh_kem (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL REFERENCES khach_hang(id),
            ten_tep       TEXT NOT NULL,
            duong_dan     TEXT NOT NULL,
            kich_thuoc    INTEGER NOT NULL,   -- byte
            nguoi_tai_len_id INTEGER REFERENCES nguoi_dung(id),
            ngay_tai_len  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS chi_muc_tep_kh ON tep_dinh_kem(khach_hang_id);
        """
    )

    # ----- Người dùng mẫu để demo phân quyền -----
    so_luong = db.execute("SELECT COUNT(*) FROM nguoi_dung").fetchone()[0]
    if so_luong == 0:
        db.executemany(
            "INSERT INTO nguoi_dung (ho_ten, vai_tro, nhom) VALUES (?, ?, ?)",
            [
                ("Nguyễn Quản Trị", "Quản trị hệ thống", "Ban điều hành"),   # id = 1
                ("Lê Trưởng Nhóm", "Trưởng nhóm", "Nhóm kinh doanh 1"),      # id = 2
                ("Trần Nhân Viên A", "Nhân viên kinh doanh", "Nhóm kinh doanh 1"),  # id = 3
                ("Phạm Nhân Viên B", "Nhân viên kinh doanh", "Nhóm kinh doanh 2"),  # id = 4
            ],
        )
    db.commit()
    db.close()
