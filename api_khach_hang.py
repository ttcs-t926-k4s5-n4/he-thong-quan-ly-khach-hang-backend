# -*- coding: utf-8 -*-
"""
[SCRUM-69] QUẢN LÝ HỒ SƠ KHÁCH HÀNG DOANH NGHIỆP
User story: "Là Nhân viên kinh doanh, tôi muốn quản lý hồ sơ khách hàng doanh
nghiệp, để có một danh sách khách chuẩn thay vì file Excel riêng của từng người."

Tiêu chí hoàn thành:
  1. Khai báo tên công ty, mã số thuế, ngành nghề, quy mô, website, địa chỉ,
     người sở hữu                                   -> POST /api/khach-hang
  2. Mã số thuế nếu có thì phải là duy nhất         -> kiểm tra khi tạo/sửa
  3. Khách hàng có trạng thái: Tiềm năng, Đang giao dịch, Khách hàng,
     Ngừng hợp tác                                  -> trường trang_thai + PUT cập nhật
  4. Nhân viên chỉ thấy khách hàng mình sở hữu;
     trưởng nhóm thấy toàn nhóm                     -> GET /api/khach-hang (lọc theo quyền)
"""
from flask import Blueprint, request, jsonify

from cau_hinh import (
    CAC_TRANG_THAI_KHACH_HANG,
    TRANG_THAI_MAC_DINH,
    VAI_TRO_QUAN_TRI,
    MAU_MA_SO_THUE,
)
from co_so_du_lieu import ket_noi_csdl, bay_gio, ghi_hoat_dong
from xac_thuc import lay_nguoi_dung_hien_tai, dieu_kien_pham_vi_xem, lay_khach_hang_neu_duoc_xem

api_khach_hang = Blueprint("api_khach_hang", __name__)


def chuyen_khach_hang_thanh_json(kh) -> dict:
    return {
        "id": kh["id"],
        "ten_cong_ty": kh["ten_cong_ty"],
        "ma_so_thue": kh["ma_so_thue"],
        "nganh_nghe": kh["nganh_nghe"],
        "quy_mo": kh["quy_mo"],
        "website": kh["website"],
        "dia_chi": kh["dia_chi"],
        "nguoi_so_huu": {
            "id": kh["nguoi_so_huu_id"],
            "ho_ten": kh["ten_nguoi_so_huu"] if "ten_nguoi_so_huu" in kh.keys() else None,
            "nhom": kh["nhom_nguoi_so_huu"] if "nhom_nguoi_so_huu" in kh.keys() else None,
        },
        "trang_thai": kh["trang_thai"],
        "ngay_tao": kh["ngay_tao"],
    }


def kiem_tra_ma_so_thue(db, ma_so_thue, bo_qua_id=None):
    """[Tiêu chí 2] MST nếu có phải đúng định dạng và DUY NHẤT. Trả về thông báo lỗi hoặc None."""
    if not ma_so_thue:
        return None
    if not MAU_MA_SO_THUE.fullmatch(ma_so_thue):
        return (
            f"Mã số thuế '{ma_so_thue}' sai định dạng. "
            "Mã số thuế Việt Nam gồm 10 chữ số, hoặc 10 chữ số kèm mã chi nhánh (ví dụ: 0101243150 hoặc 0101243150-001)."
        )
    cau_lenh = "SELECT id, ten_cong_ty FROM khach_hang WHERE ma_so_thue = ?"
    tham_so = [ma_so_thue]
    if bo_qua_id is not None:
        cau_lenh += " AND id <> ?"
        tham_so.append(bo_qua_id)
    trung = db.execute(cau_lenh, tham_so).fetchone()
    if trung:
        return (
            f"Mã số thuế '{ma_so_thue}' đã tồn tại trong hệ thống "
            f"(thuộc khách hàng '{trung['ten_cong_ty']}', id = {trung['id']}). Mã số thuế phải là duy nhất."
        )
    return None


@api_khach_hang.post("/api/khach-hang")
def tao_khach_hang():
    """[Tiêu chí 1+2+3] Tạo hồ sơ khách hàng doanh nghiệp."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi

    du_lieu = request.get_json(silent=True)
    if du_lieu is None:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Dữ liệu gửi lên phải ở dạng JSON. Ví dụ: {\"ten_cong_ty\": \"Công ty ABC\"}.",
        }), 400

    ten_cong_ty = str(du_lieu.get("ten_cong_ty") or "").strip()
    if not ten_cong_ty:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Thiếu tên công ty. Trường 'ten_cong_ty' là bắt buộc.",
        }), 400

    ma_so_thue = str(du_lieu.get("ma_so_thue") or "").strip() or None
    db = ket_noi_csdl()
    loi_mst = kiem_tra_ma_so_thue(db, ma_so_thue)
    if loi_mst:
        return jsonify({"thanh_cong": False, "thong_bao": loi_mst}), 400

    trang_thai = str(du_lieu.get("trang_thai") or TRANG_THAI_MAC_DINH).strip()
    if trang_thai not in CAC_TRANG_THAI_KHACH_HANG:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                f"Trạng thái '{trang_thai}' không hợp lệ. "
                f"Chỉ chấp nhận: {', '.join(CAC_TRANG_THAI_KHACH_HANG)}."
            ),
        }), 400

