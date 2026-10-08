# -*- coding: utf-8 -*-
"""
[SCRUM-60] XEM VÀ CẬP NHẬT HỒ SƠ CÁ NHÂN
User story: "Là người dùng của hệ thống, tôi muốn xem và cập nhật hồ sơ cá nhân,
để chữ ký email của tôi luôn đúng khi gửi báo giá cho khách."

Tiêu chí hoàn thành:
  1. Sửa được họ tên, số điện thoại, chữ ký email  -> GET /api/ho-so, PUT /api/ho-so
  2. Không tự đổi được email, nhóm và vai trò       -> gửi lên sẽ bị chặn (403)
  3. Kiểm tra định dạng số điện thoại Việt Nam
"""
from flask import Blueprint, request, jsonify

from cau_hinh import MAU_SDT_VIET_NAM
from co_so_du_lieu import ket_noi_csdl, chuyen_thanh_tu_dien
from xac_thuc import lay_nguoi_dung_hien_tai

api_ho_so = Blueprint("api_ho_so", __name__)


@api_ho_so.get("/api/ho-so")
def xem_ho_so():
    """Xem hồ sơ cá nhân của người dùng hiện tại (theo header X-User-Id)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    return jsonify({"thanh_cong": True, "ho_so": chuyen_thanh_tu_dien(nguoi_dung)})


@api_ho_so.put("/api/ho-so")
def cap_nhat_ho_so():
    """Cập nhật hồ sơ cá nhân theo đúng 3 tiêu chí của SCRUM-60."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi

    du_lieu = request.get_json(silent=True)
    if du_lieu is None:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Dữ liệu gửi lên phải ở dạng JSON. Ví dụ: {\"ho_ten\": \"Tên mới\"}.",
        }), 400

    # --- [Tiêu chí 2] Chặn các trường không được phép tự thay đổi ---
    truong_bi_cam = {"email", "nhom", "vai_tro"}
    truong_vi_pham = sorted(truong_bi_cam.intersection(du_lieu.keys()))
    if truong_vi_pham:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                "Bạn không được tự thay đổi các trường: "
                + ", ".join(truong_vi_pham)
                + ". Chỉ Quản trị hệ thống mới có quyền thay đổi email, nhóm và vai trò."
            ),
        }), 403

    truong_cho_phep = {"ho_ten", "so_dien_thoai", "chu_ky_email"}
    truong_khong_ho_tro = sorted(set(du_lieu.keys()) - truong_cho_phep)
