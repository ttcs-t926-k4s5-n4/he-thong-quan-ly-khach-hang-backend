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
    return jsonify({
        "thanh_cong": True,
        "thong_bao": f"Đã tải lên tệp '{ten_goc}' ({len(noi_dung_tep) / 1024:.1f} KB).",
        "tep_id": con_tro.lastrowid,
    }), 201


@api_trang_360.get("/api/tep-dinh-kem/<int:tep_id>")
def tai_xuong_tep(tep_id):
    """Tải xuống một tệp đính kèm."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    db = ket_noi_csdl()
    tep = db.execute("SELECT * FROM tep_dinh_kem WHERE id = ?", (tep_id,)).fetchone()
    if tep is None:
        return jsonify({"thanh_cong": False, "thong_bao": f"Không tìm thấy tệp có id = {tep_id}."}), 404
    _, loi = lay_khach_hang_neu_duoc_xem(tep["khach_hang_id"], nguoi_dung)
    if loi:
        return loi
    if not os.path.exists(tep["duong_dan"]):
        return jsonify({"thanh_cong": False, "thong_bao": "Tệp không còn tồn tại trên máy chủ."}), 404
    return send_file(tep["duong_dan"], as_attachment=True, download_name=tep["ten_tep"])


# ============================================================================
# [SCRUM-71] TRANG 360 - GOM TOÀN BỘ BỐI CẢNH VỀ MỘT TRANG
# ============================================================================
@api_trang_360.get("/api/khach-hang/<int:khach_hang_id>/trang-360")
def trang_360(khach_hang_id):
    """
    [Tiêu chí 1] Một trang gom đủ 5 khối: thông tin công ty, người liên hệ,
    cơ hội (đang mở + đã đóng), dòng thời gian hoạt động, tệp đính kèm.
    [Tiêu chí 2] Tổng giá trị đã ký và giá trị cơ hội đang mở.
    [Tiêu chí 3] Đo thời gian tải trả về trong kết quả (yêu cầu < 1,5 giây với 500 hoạt động).
    """
    bat_dau = time.perf_counter()

    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    khach_hang, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    try:
        gioi_han = int(request.args.get("gioi_han_hoat_dong", GIOI_HAN_HOAT_DONG_MAC_DINH))
    except ValueError:
        gioi_han = GIOI_HAN_HOAT_DONG_MAC_DINH
    gioi_han = max(1, min(gioi_han, 2000))

    db = ket_noi_csdl()

    # ----- Khối 1: Thông tin công ty -----
    thong_tin_cong_ty = {
        "id": khach_hang["id"],
        "ten_cong_ty": khach_hang["ten_cong_ty"],
        "ma_so_thue": khach_hang["ma_so_thue"],
        "nganh_nghe": khach_hang["nganh_nghe"],
        "quy_mo": khach_hang["quy_mo"],
        "website": khach_hang["website"],
        "dia_chi": khach_hang["dia_chi"],
        "trang_thai": khach_hang["trang_thai"],
        "nguoi_so_huu": {
            "id": khach_hang["nguoi_so_huu_id"],
            "ho_ten": khach_hang["ten_nguoi_so_huu"],
            "nhom": khach_hang["nhom_nguoi_so_huu"],
        },
        "ngay_tao": khach_hang["ngay_tao"],
    }

    # ----- Khối 2: Danh sách người liên hệ -----
    nguoi_lien_he = db.execute(
        """SELECT * FROM nguoi_lien_he WHERE khach_hang_id = ?
           ORDER BY la_dau_moi_chinh DESC, id""",
        (khach_hang_id,),
    ).fetchall()

    # ----- Khối 3: Cơ hội đang mở và đã đóng + [Tiêu chí 2] hai con số tổng -----
    co_hoi = db.execute(
        "SELECT * FROM co_hoi WHERE khach_hang_id = ? ORDER BY id DESC",
        (khach_hang_id,),
    ).fetchall()
    co_hoi_dang_mo = [c for c in co_hoi if c["trang_thai"] == "Đang mở"]
    co_hoi_da_dong = [c for c in co_hoi if c["trang_thai"] != "Đang mở"]
    tong_gia_tri_da_ky = sum(c["gia_tri"] for c in co_hoi if c["trang_thai"] == "Đã thắng")
    tong_gia_tri_dang_mo = sum(c["gia_tri"] for c in co_hoi_dang_mo)

    def chuyen_co_hoi(c):
        return {
            "id": c["id"], "ten_co_hoi": c["ten_co_hoi"],
            "gia_tri": c["gia_tri"], "trang_thai": c["trang_thai"],
            "ngay_tao": c["ngay_tao"],
        }

    # ----- Khối 4: Dòng thời gian hoạt động (dùng chỉ mục, mới nhất trước) -----
    hoat_dong = db.execute(
        """SELECT hd.id, hd.loai, hd.noi_dung, hd.thoi_gian, nd.ho_ten AS nguoi_thuc_hien
           FROM hoat_dong hd LEFT JOIN nguoi_dung nd ON nd.id = hd.nguoi_thuc_hien_id
           WHERE hd.khach_hang_id = ?
           ORDER BY hd.thoi_gian DESC, hd.id DESC
           LIMIT ?""",
        (khach_hang_id, gioi_han),
    ).fetchall()
    tong_so_hoat_dong = db.execute(
        "SELECT COUNT(*) FROM hoat_dong WHERE khach_hang_id = ?", (khach_hang_id,)
    ).fetchone()[0]

    # ----- Khối 5: Tệp đính kèm -----
    tep_dinh_kem = db.execute(
        "SELECT * FROM tep_dinh_kem WHERE khach_hang_id = ? ORDER BY id DESC",
        (khach_hang_id,),
    ).fetchall()

    thoi_gian_tai = time.perf_counter() - bat_dau

    return jsonify({
        "thanh_cong": True,
        "trang_360": {
            "thong_tin_cong_ty": thong_tin_cong_ty,
            "nguoi_lien_he": {
                "tong_so": len(nguoi_lien_he),
                "danh_sach": [chuyen_nlh_thanh_json(n) for n in nguoi_lien_he],
            },
            "co_hoi": {
                # [Tiêu chí 2] Hai con số tổng hiển thị ngay đầu khối
                "tong_gia_tri_da_ky": tong_gia_tri_da_ky,
                "tong_gia_tri_dang_mo": tong_gia_tri_dang_mo,
                "dang_mo": [chuyen_co_hoi(c) for c in co_hoi_dang_mo],
                "da_dong": [chuyen_co_hoi(c) for c in co_hoi_da_dong],
            },
            "dong_thoi_gian": {
                "tong_so_hoat_dong": tong_so_hoat_dong,
                "so_hoat_dong_tra_ve": len(hoat_dong),
                "danh_sach": [
                    {
                        "id": h["id"], "loai": h["loai"], "noi_dung": h["noi_dung"],
                        "thoi_gian": h["thoi_gian"],
                        "nguoi_thuc_hien": h["nguoi_thuc_hien"],
                    }
                    for h in hoat_dong
                ],
            },
            "tep_dinh_kem": {
                "tong_so": len(tep_dinh_kem),
                "danh_sach": [
                    {
                        "id": t["id"], "ten_tep": t["ten_tep"],
                        "kich_thuoc_kb": round(t["kich_thuoc"] / 1024, 1),
                        "ngay_tai_len": t["ngay_tai_len"],
                        "tai_xuong": f"GET /api/tep-dinh-kem/{t['id']}",
                    }
                    for t in tep_dinh_kem
                ],
            },
        },
        # [Tiêu chí 3] Thời gian tải đo tại máy chủ
        "hieu_nang": {
            "thoi_gian_tai_giay": round(thoi_gian_tai, 4),
            "dat_tieu_chi_duoi_1_5_giay": thoi_gian_tai < THOI_GIAN_TAI_TOI_DA_GIAY,
        },
    })
