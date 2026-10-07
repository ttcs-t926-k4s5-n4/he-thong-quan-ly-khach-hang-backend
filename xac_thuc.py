# -*- coding: utf-8 -*-
"""
XÁC THỰC VÀ PHÂN QUYỀN
- Xác thực demo: header X-User-Id hoặc tham số ?user_id= trên URL (để test nhanh trên trình duyệt).
- Phân quyền xem khách hàng theo tiêu chí SCRUM-69:
    + Nhân viên kinh doanh: chỉ thấy khách hàng MÌNH sở hữu.
    + Trưởng nhóm: thấy khách hàng của TOÀN NHÓM mình.
    + Quản trị hệ thống: thấy tất cả.
"""
from flask import request, jsonify

from cau_hinh import VAI_TRO_QUAN_TRI, VAI_TRO_TRUONG_NHOM
from co_so_du_lieu import ket_noi_csdl


def lay_nguoi_dung_hien_tai():
    """Trả về (nguoi_dung, loi). Nếu lỗi thì nguoi_dung = None."""
    ma_nguoi_dung = request.headers.get("X-User-Id") or request.args.get("user_id")
    if not ma_nguoi_dung:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": "Thiếu thông tin đăng nhập. Hãy gửi header X-User-Id hoặc thêm ?user_id= vào URL (ví dụ: 3).",
            }),
            401,
        )
    db = ket_noi_csdl()
    nguoi_dung = db.execute(
        "SELECT * FROM nguoi_dung WHERE id = ?", (ma_nguoi_dung,)
    ).fetchone()
    if nguoi_dung is None:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": f"Không tìm thấy người dùng có id = {ma_nguoi_dung}.",
            }),
            404,
        )
    return nguoi_dung, None


def dieu_kien_pham_vi_xem(nguoi_dung):
    """
    Trả về (mệnh_đề_SQL, tham_số) để lọc danh sách khách hàng theo quyền.
    Dùng với câu lệnh đã JOIN bảng nguoi_dung (bí danh nsh = người sở hữu).
    """
    if nguoi_dung["vai_tro"] == VAI_TRO_QUAN_TRI:
        return "1 = 1", []
    if nguoi_dung["vai_tro"] == VAI_TRO_TRUONG_NHOM:
        return "nsh.nhom = ?", [nguoi_dung["nhom"]]
    return "kh.nguoi_so_huu_id = ?", [nguoi_dung["id"]]


def lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung):
    """
    Lấy khách hàng theo id và kiểm tra quyền xem của người dùng hiện tại.
    Trả về (khach_hang, loi). Nếu không có quyền -> lỗi 403 tiếng Việt.
    """
    db = ket_noi_csdl()
    khach_hang = db.execute(
        """SELECT kh.*, nsh.ho_ten AS ten_nguoi_so_huu, nsh.nhom AS nhom_nguoi_so_huu
           FROM khach_hang kh JOIN nguoi_dung nsh ON nsh.id = kh.nguoi_so_huu_id
           WHERE kh.id = ?""",
        (khach_hang_id,),
    ).fetchone()
    if khach_hang is None:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": f"Không tìm thấy khách hàng có id = {khach_hang_id}.",
            }),
            404,
        )

    vai_tro = nguoi_dung["vai_tro"]
    duoc_xem = (
        vai_tro == VAI_TRO_QUAN_TRI
        or (vai_tro == VAI_TRO_TRUONG_NHOM and khach_hang["nhom_nguoi_so_huu"] == nguoi_dung["nhom"])
        or khach_hang["nguoi_so_huu_id"] == nguoi_dung["id"]
    )
    if not duoc_xem:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": (
                    "Bạn không có quyền xem khách hàng này. "
                    "Nhân viên chỉ thấy khách hàng mình sở hữu; trưởng nhóm thấy khách hàng của toàn nhóm."
                ),
            }),
            403,
        )
    return khach_hang, None
