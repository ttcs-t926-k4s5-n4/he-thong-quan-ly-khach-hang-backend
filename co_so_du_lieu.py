# -*- coding: utf-8 -*-
"""
CƠ SỞ DỮ LIỆU (SQLite)
Kết nối, khởi tạo bảng người dùng, tạo dữ liệu mẫu và các hàm dùng chung.
"""
import os
import sqlite3
import hashlib
from datetime import datetime

from flask import g

from cau_hinh import TEP_CSDL, THU_MUC_ANH


def ket_noi_csdl():
    """Lấy kết nối SQLite cho mỗi request (dùng chung trong 1 request)."""
    if "db" not in g:
        g.db = sqlite3.connect(TEP_CSDL)
        g.db.row_factory = sqlite3.Row
    return g.db


def dong_csdl(_=None):
    """Đóng kết nối khi kết thúc request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ma_hoa_mat_khau(mat_khau: str) -> str:
    """Băm mật khẩu bằng SHA-256 (đơn giản cho demo)."""
    return hashlib.sha256(mat_khau.encode("utf-8")).hexdigest()


def khoi_tao_csdl():
    """Tạo bảng người dùng và 2 tài khoản mẫu ban đầu."""
    os.makedirs(THU_MUC_ANH, exist_ok=True)
    db = sqlite3.connect(TEP_CSDL)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS nguoi_dung (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten          TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            so_dien_thoai   TEXT,
            nhom            TEXT,
            vai_tro         TEXT NOT NULL,
            chu_ky_email    TEXT DEFAULT '',
            mat_khau        TEXT NOT NULL,
            anh_dai_dien    TEXT,
            anh_thu_nho     TEXT,
            ngay_tao        TEXT NOT NULL
        )
        """
    )
    so_luong = db.execute("SELECT COUNT(*) FROM nguoi_dung").fetchone()[0]
    if so_luong == 0:
        bay_gio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.executemany(
            """INSERT INTO nguoi_dung
               (ho_ten, email, so_dien_thoai, nhom, vai_tro, chu_ky_email, mat_khau, ngay_tao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    "Nguyễn Quản Trị", "admin@congty.vn", "0912345678",
                    "Ban điều hành", "Quản trị hệ thống",
                    "Trân trọng,\nNguyễn Quản Trị - Quản trị hệ thống",
                    ma_hoa_mat_khau("admin123"), bay_gio,
                ),
                (
                    "Trần Văn Nhân Viên", "nhanvien@congty.vn", "0987654321",
                    "Nhóm kinh doanh 1", "Nhân viên kinh doanh",
                    "Trân trọng,\nTrần Văn Nhân Viên - Nhân viên kinh doanh",
                    ma_hoa_mat_khau("123456"), bay_gio,
                ),
            ],
        )
    db.commit()
    db.close()


def chuyen_thanh_tu_dien(nguoi_dung) -> dict:
    """Chuyển bản ghi người dùng thành JSON trả về (ẩn mật khẩu)."""
    return {
        "id": nguoi_dung["id"],
        "ho_ten": nguoi_dung["ho_ten"],
        "email": nguoi_dung["email"],
        "so_dien_thoai": nguoi_dung["so_dien_thoai"],
        "nhom": nguoi_dung["nhom"],
        "vai_tro": nguoi_dung["vai_tro"],
        "chu_ky_email": nguoi_dung["chu_ky_email"],
        "co_anh_dai_dien": bool(nguoi_dung["anh_dai_dien"]),
        "ngay_tao": nguoi_dung["ngay_tao"],
    }
