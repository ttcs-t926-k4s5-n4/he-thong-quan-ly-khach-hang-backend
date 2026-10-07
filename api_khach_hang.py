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

    # Người sở hữu: mặc định là người tạo; Quản trị hệ thống được gán cho người khác
    nguoi_so_huu_id = nguoi_dung["id"]
    if du_lieu.get("nguoi_so_huu_id") and nguoi_dung["vai_tro"] == VAI_TRO_QUAN_TRI:
        nguoi_so_huu_id = int(du_lieu["nguoi_so_huu_id"])
        if db.execute("SELECT id FROM nguoi_dung WHERE id = ?", (nguoi_so_huu_id,)).fetchone() is None:
            return jsonify({
                "thanh_cong": False,
                "thong_bao": f"Không tìm thấy người sở hữu có id = {nguoi_so_huu_id}.",
            }), 400

    con_tro = db.execute(
        """INSERT INTO khach_hang
           (ten_cong_ty, ma_so_thue, nganh_nghe, quy_mo, website, dia_chi,
            nguoi_so_huu_id, trang_thai, ngay_tao)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ten_cong_ty, ma_so_thue,
            str(du_lieu.get("nganh_nghe") or "").strip(),
            str(du_lieu.get("quy_mo") or "").strip(),
            str(du_lieu.get("website") or "").strip(),
            str(du_lieu.get("dia_chi") or "").strip(),
            nguoi_so_huu_id, trang_thai, bay_gio(),
        ),
    )
    khach_hang_id = con_tro.lastrowid
    ghi_hoat_dong(db, khach_hang_id, "Hệ thống",
                  f"Tạo hồ sơ khách hàng '{ten_cong_ty}' với trạng thái '{trang_thai}'.",
                  nguoi_dung["id"])
    db.commit()

    return jsonify({
        "thanh_cong": True,
        "thong_bao": f"Đã tạo hồ sơ khách hàng '{ten_cong_ty}' (id = {khach_hang_id}).",
        "khach_hang_id": khach_hang_id,
    }), 201


@api_khach_hang.get("/api/khach-hang")
def danh_sach_khach_hang():
    """
    [Tiêu chí 4] Danh sách khách hàng lọc theo quyền:
    - Nhân viên: chỉ khách hàng mình sở hữu.
    - Trưởng nhóm: khách hàng của toàn nhóm.
    - Quản trị hệ thống: tất cả.
    """
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi

    db = ket_noi_csdl()
    menh_de, tham_so = dieu_kien_pham_vi_xem(nguoi_dung)
    danh_sach = db.execute(
        f"""SELECT kh.*, nsh.ho_ten AS ten_nguoi_so_huu, nsh.nhom AS nhom_nguoi_so_huu
            FROM khach_hang kh JOIN nguoi_dung nsh ON nsh.id = kh.nguoi_so_huu_id
            WHERE {menh_de} ORDER BY kh.id""",
        tham_so,
    ).fetchall()

    return jsonify({
        "thanh_cong": True,
        "pham_vi_xem": (
            "Tất cả khách hàng" if nguoi_dung["vai_tro"] == VAI_TRO_QUAN_TRI
            else f"Khách hàng của {nguoi_dung['nhom']}" if nguoi_dung["vai_tro"] == "Trưởng nhóm"
            else "Khách hàng do bạn sở hữu"
        ),
        "tong_so": len(danh_sach),
        "danh_sach": [chuyen_khach_hang_thanh_json(kh) for kh in danh_sach],
    })


@api_khach_hang.get("/api/khach-hang/<int:khach_hang_id>")
def xem_khach_hang(khach_hang_id):
    """Xem chi tiết một khách hàng (có kiểm tra quyền theo tiêu chí 4)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    khach_hang, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi
    return jsonify({"thanh_cong": True, "khach_hang": chuyen_khach_hang_thanh_json(khach_hang)})


@api_khach_hang.put("/api/khach-hang/<int:khach_hang_id>")
def cap_nhat_khach_hang(khach_hang_id):
    """Cập nhật hồ sơ: các trường khai báo + trạng thái (kiểm tra MST duy nhất)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    khach_hang, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True)
    if not du_lieu:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Không có dữ liệu JSON nào để cập nhật.",
        }), 400

    db = ket_noi_csdl()
    cap_nhat = {}

    if "ten_cong_ty" in du_lieu:
        ten_moi = str(du_lieu["ten_cong_ty"]).strip()
        if not ten_moi:
            return jsonify({"thanh_cong": False, "thong_bao": "Tên công ty không được để trống."}), 400
        cap_nhat["ten_cong_ty"] = ten_moi

    if "ma_so_thue" in du_lieu:
        mst_moi = str(du_lieu["ma_so_thue"] or "").strip() or None
        loi_mst = kiem_tra_ma_so_thue(db, mst_moi, bo_qua_id=khach_hang_id)
        if loi_mst:
            return jsonify({"thanh_cong": False, "thong_bao": loi_mst}), 400
        cap_nhat["ma_so_thue"] = mst_moi

    if "trang_thai" in du_lieu:
        trang_thai_moi = str(du_lieu["trang_thai"]).strip()
        if trang_thai_moi not in CAC_TRANG_THAI_KHACH_HANG:
            return jsonify({
                "thanh_cong": False,
                "thong_bao": (
                    f"Trạng thái '{trang_thai_moi}' không hợp lệ. "
                    f"Chỉ chấp nhận: {', '.join(CAC_TRANG_THAI_KHACH_HANG)}."
                ),
            }), 400
        cap_nhat["trang_thai"] = trang_thai_moi

    for truong in ("nganh_nghe", "quy_mo", "website", "dia_chi"):
        if truong in du_lieu:
            cap_nhat[truong] = str(du_lieu[truong] or "").strip()

    if not cap_nhat:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                "Không có trường hợp lệ nào để cập nhật. Các trường được hỗ trợ: "
                "ten_cong_ty, ma_so_thue, nganh_nghe, quy_mo, website, dia_chi, trang_thai."
            ),
        }), 400

    cau_lenh = ", ".join(f"{ten} = ?" for ten in cap_nhat)
    db.execute(
        f"UPDATE khach_hang SET {cau_lenh} WHERE id = ?",
        (*cap_nhat.values(), khach_hang_id),
    )
    if "trang_thai" in cap_nhat:
        ghi_hoat_dong(db, khach_hang_id, "Hệ thống",
                      f"Chuyển trạng thái khách hàng từ '{khach_hang['trang_thai']}' sang '{cap_nhat['trang_thai']}'.",
                      nguoi_dung["id"])
    db.commit()

    kh_moi = db.execute(
        """SELECT kh.*, nsh.ho_ten AS ten_nguoi_so_huu, nsh.nhom AS nhom_nguoi_so_huu
           FROM khach_hang kh JOIN nguoi_dung nsh ON nsh.id = kh.nguoi_so_huu_id
           WHERE kh.id = ?""",
        (khach_hang_id,),
    ).fetchone()
    return jsonify({
        "thanh_cong": True,
        "thong_bao": "Cập nhật khách hàng thành công. Các trường đã thay đổi: " + ", ".join(cap_nhat.keys()) + ".",
        "khach_hang": chuyen_khach_hang_thanh_json(kh_moi),
    })
