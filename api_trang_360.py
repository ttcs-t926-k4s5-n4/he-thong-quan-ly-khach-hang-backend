# -*- coding: utf-8 -*-
"""
[SCRUM-71] TRANG 360 CỦA KHÁCH HÀNG
User story: "Là Nhân viên kinh doanh, tôi muốn xem trang 360 của một khách hàng,
để nắm toàn bộ bối cảnh trước cuộc gặp mà không phải mở năm chỗ khác nhau."

Tiêu chí hoàn thành:
  1. Một trang gom: thông tin công ty, danh sách người liên hệ, cơ hội đang mở
     và đã đóng, dòng thời gian hoạt động, tệp đính kèm
                                    -> GET /api/khach-hang/<id>/trang-360
  2. Hiển thị tổng giá trị đã ký và giá trị cơ hội đang mở
                                    -> hai trường tổng trong kết quả
  3. Tải xong dưới 1,5 giây với 500 hoạt động
                                    -> chỉ mục CSDL + đo và trả về thời gian tải

File này cũng cung cấp các API tạo dữ liệu cho trang 360:
  - POST /api/khach-hang/<id>/co-hoi        (cơ hội bán hàng)
  - POST /api/khach-hang/<id>/hoat-dong     (hoạt động: ghi chú, cuộc gọi, email...)
  - POST /api/khach-hang/<id>/tep-dinh-kem  (tải tệp đính kèm, tối đa 10MB)
"""
import os
import time

from flask import Blueprint, request, jsonify, send_file

from cau_hinh import (
    CAC_TRANG_THAI_CO_HOI,
    GIOI_HAN_HOAT_DONG_MAC_DINH,
    THOI_GIAN_TAI_TOI_DA_GIAY,
    THU_MUC_TEP_DINH_KEM,
    KICH_THUOC_TEP_TOI_DA,
)
from co_so_du_lieu import ket_noi_csdl, bay_gio, ghi_hoat_dong
from xac_thuc import lay_nguoi_dung_hien_tai, lay_khach_hang_neu_duoc_xem
from api_nguoi_lien_he import chuyen_nlh_thanh_json

api_trang_360 = Blueprint("api_trang_360", __name__)


# ============================================================================
# CÁC API TẠO DỮ LIỆU CHO TRANG 360
# ============================================================================
@api_trang_360.post("/api/khach-hang/<int:khach_hang_id>/co-hoi")
def tao_co_hoi(khach_hang_id):
    """Tạo cơ hội bán hàng (phục vụ tổng giá trị đã ký / đang mở ở trang 360)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    _, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True) or {}
    ten_co_hoi = str(du_lieu.get("ten_co_hoi") or "").strip()
    if not ten_co_hoi:
        return jsonify({"thanh_cong": False, "thong_bao": "Thiếu tên cơ hội ('ten_co_hoi')."}), 400

    try:
        gia_tri = float(du_lieu.get("gia_tri") or 0)
        if gia_tri < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Giá trị cơ hội ('gia_tri') phải là một số không âm (đơn vị VNĐ).",
        }), 400

    trang_thai = str(du_lieu.get("trang_thai") or "Đang mở").strip()
    if trang_thai not in CAC_TRANG_THAI_CO_HOI:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": f"Trạng thái cơ hội '{trang_thai}' không hợp lệ. Chỉ chấp nhận: {', '.join(CAC_TRANG_THAI_CO_HOI)}.",
        }), 400

    db = ket_noi_csdl()
    con_tro = db.execute(
        """INSERT INTO co_hoi (khach_hang_id, ten_co_hoi, gia_tri, trang_thai, ngay_tao)
           VALUES (?, ?, ?, ?, ?)""",
        (khach_hang_id, ten_co_hoi, gia_tri, trang_thai, bay_gio()),
    )
    ghi_hoat_dong(db, khach_hang_id, "Hệ thống",
                  f"Tạo cơ hội '{ten_co_hoi}' trị giá {gia_tri:,.0f} VNĐ ({trang_thai}).",
                  nguoi_dung["id"])
    db.commit()
    return jsonify({
        "thanh_cong": True,
        "thong_bao": f"Đã tạo cơ hội '{ten_co_hoi}' ({trang_thai}).",
        "co_hoi_id": con_tro.lastrowid,
    }), 201


@api_trang_360.post("/api/khach-hang/<int:khach_hang_id>/hoat-dong")
def them_hoat_dong(khach_hang_id):
    """Thêm hoạt động vào dòng thời gian (ghi chú, cuộc gọi, email, cuộc họp...)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    _, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True) or {}
    noi_dung = str(du_lieu.get("noi_dung") or "").strip()
    if not noi_dung:
        return jsonify({"thanh_cong": False, "thong_bao": "Thiếu nội dung hoạt động ('noi_dung')."}), 400
    loai = str(du_lieu.get("loai") or "Ghi chú").strip()

    db = ket_noi_csdl()
    ghi_hoat_dong(db, khach_hang_id, loai, noi_dung, nguoi_dung["id"])
    db.commit()
    return jsonify({"thanh_cong": True, "thong_bao": f"Đã ghi hoạt động '{loai}' vào dòng thời gian."}), 201


@api_trang_360.post("/api/khach-hang/<int:khach_hang_id>/tep-dinh-kem")
def tai_tep_dinh_kem(khach_hang_id):
    """Tải tệp đính kèm cho khách hàng (tối đa 10MB, hiển thị ở trang 360)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    _, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    if "tep" not in request.files:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Chưa chọn tệp. Hãy gửi form-data với khóa 'tep'.",
        }), 400
    tep = request.files["tep"]
    ten_goc = os.path.basename(tep.filename or "").strip()
    if not ten_goc:
        return jsonify({"thanh_cong": False, "thong_bao": "Tên tệp không hợp lệ."}), 400

    noi_dung_tep = tep.read()
    if len(noi_dung_tep) == 0:
        return jsonify({"thanh_cong": False, "thong_bao": "Tệp rỗng."}), 400
    if len(noi_dung_tep) > KICH_THUOC_TEP_TOI_DA:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                f"Tệp có dung lượng {len(noi_dung_tep) / (1024 * 1024):.2f}MB, "
                "vượt quá giới hạn 10MB cho tệp đính kèm."
            ),
        }), 400

    os.makedirs(THU_MUC_TEP_DINH_KEM, exist_ok=True)
    ten_luu = f"kh{khach_hang_id}_{int(time.time() * 1000)}_{ten_goc}"
    duong_dan = os.path.join(THU_MUC_TEP_DINH_KEM, ten_luu)
    with open(duong_dan, "wb") as f:
        f.write(noi_dung_tep)

    db = ket_noi_csdl()
    con_tro = db.execute(
        """INSERT INTO tep_dinh_kem
           (khach_hang_id, ten_tep, duong_dan, kich_thuoc, nguoi_tai_len_id, ngay_tai_len)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (khach_hang_id, ten_goc, duong_dan, len(noi_dung_tep), nguoi_dung["id"], bay_gio()),
    )
    ghi_hoat_dong(db, khach_hang_id, "Hệ thống",
                  f"Tải lên tệp đính kèm '{ten_goc}'.", nguoi_dung["id"])
    db.commit()
