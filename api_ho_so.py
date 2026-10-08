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
    if truong_khong_ho_tro:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                "Trường không được hỗ trợ: " + ", ".join(truong_khong_ho_tro)
                + ". Chỉ được cập nhật: ho_ten, so_dien_thoai, chu_ky_email."
            ),
        }), 400
    if not du_lieu:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Không có dữ liệu nào để cập nhật. Hãy gửi ít nhất một trong: ho_ten, so_dien_thoai, chu_ky_email.",
        }), 400

    cap_nhat = {}

    # --- [Tiêu chí 1] Họ tên ---
    if "ho_ten" in du_lieu:
        ho_ten_moi = str(du_lieu["ho_ten"]).strip()
        if not ho_ten_moi:
            return jsonify({
                "thanh_cong": False,
                "thong_bao": "Họ tên không được để trống.",
            }), 400
        cap_nhat["ho_ten"] = ho_ten_moi

    # --- [Tiêu chí 3] Kiểm tra định dạng số điện thoại Việt Nam ---
    if "so_dien_thoai" in du_lieu:
        sdt_moi = str(du_lieu["so_dien_thoai"]).strip()
        if sdt_moi and not MAU_SDT_VIET_NAM.fullmatch(sdt_moi):
            return jsonify({
                "thanh_cong": False,
                "thong_bao": (
                    f"Số điện thoại '{sdt_moi}' không đúng định dạng Việt Nam. "
                    "Số hợp lệ bắt đầu bằng 0 hoặc +84 và gồm 10 chữ số, ví dụ: 0912345678 hoặc +84912345678."
                ),
            }), 400
        cap_nhat["so_dien_thoai"] = sdt_moi

    # --- [Tiêu chí 1] Chữ ký email (dùng khi gửi báo giá cho khách) ---
    if "chu_ky_email" in du_lieu:
        cap_nhat["chu_ky_email"] = str(du_lieu["chu_ky_email"])

    db = ket_noi_csdl()
    cau_lenh = ", ".join(f"{ten} = ?" for ten in cap_nhat)
    db.execute(
        f"UPDATE nguoi_dung SET {cau_lenh} WHERE id = ?",
        (*cap_nhat.values(), nguoi_dung["id"]),
    )
    db.commit()

    ho_so_moi = db.execute(
        "SELECT * FROM nguoi_dung WHERE id = ?", (nguoi_dung["id"],)
    ).fetchone()
    return jsonify({
        "thanh_cong": True,
        "thong_bao": "Cập nhật hồ sơ thành công. Các trường đã thay đổi: " + ", ".join(cap_nhat.keys()) + ".",
        "ho_so": chuyen_thanh_tu_dien(ho_so_moi),
    })
