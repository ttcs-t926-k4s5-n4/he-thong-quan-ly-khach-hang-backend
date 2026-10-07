# -*- coding: utf-8 -*-
"""
[SCRUM-70] QUẢN LÝ NGƯỜI LIÊN HỆ VÀ VAI TRÒ TRONG QUYẾT ĐỊNH MUA
User story: "Là Nhân viên kinh doanh, tôi muốn quản lý người liên hệ và vai trò
của họ trong quyết định mua, để biết phải thuyết phục ai và ai là người có thể
cản thương vụ."

Tiêu chí hoàn thành:
  1. Mỗi khách hàng có nhiều người liên hệ, mỗi người có chức danh, email,
     số điện thoại                 -> POST/GET /api/khach-hang/<id>/nguoi-lien-he
  2. Đánh dấu vai trò trong quyết định mua: người quyết định, người ảnh hưởng,
     người dùng cuối, người cản trở -> trường vai_tro_mua + PUT cập nhật
  3. Đánh dấu một người là đầu mối chính -> PUT /api/nguoi-lien-he/<id>/dau-moi-chinh
  4. Một người liên hệ chuyển sang công ty khác thì gắn lại được sang khách hàng
     mới, giữ nguyên lịch sử        -> PUT /api/nguoi-lien-he/<id>/chuyen-cong-ty
                                      + GET /api/nguoi-lien-he/<id>/lich-su
"""
from flask import Blueprint, request, jsonify

from cau_hinh import CAC_VAI_TRO_QUYET_DINH_MUA, MAU_EMAIL, MAU_SDT_VIET_NAM
from co_so_du_lieu import ket_noi_csdl, bay_gio, ghi_hoat_dong
from xac_thuc import lay_nguoi_dung_hien_tai, lay_khach_hang_neu_duoc_xem

api_nguoi_lien_he = Blueprint("api_nguoi_lien_he", __name__)


def chuyen_nlh_thanh_json(n) -> dict:
    return {
        "id": n["id"],
        "khach_hang_id": n["khach_hang_id"],
        "ho_ten": n["ho_ten"],
        "chuc_danh": n["chuc_danh"],
        "email": n["email"],
        "so_dien_thoai": n["so_dien_thoai"],
        "vai_tro_mua": n["vai_tro_mua"],
        "la_dau_moi_chinh": bool(n["la_dau_moi_chinh"]),
        "ngay_tao": n["ngay_tao"],
    }


def kiem_tra_thong_tin_lien_he(email, so_dien_thoai, vai_tro_mua):
    """Kiểm tra định dạng email, SĐT Việt Nam và vai trò mua. Trả về thông báo lỗi hoặc None."""
    if email and not MAU_EMAIL.fullmatch(email):
        return f"Email '{email}' sai định dạng."
    if so_dien_thoai and not MAU_SDT_VIET_NAM.fullmatch(so_dien_thoai):
        return (
            f"Số điện thoại '{so_dien_thoai}' không đúng định dạng Việt Nam "
            "(bắt đầu bằng 0 hoặc +84, ví dụ 0912345678)."
        )
    if vai_tro_mua and vai_tro_mua not in CAC_VAI_TRO_QUYET_DINH_MUA:
        return (
            f"Vai trò trong quyết định mua '{vai_tro_mua}' không hợp lệ. "
            f"Chỉ chấp nhận: {', '.join(CAC_VAI_TRO_QUYET_DINH_MUA)}."
        )
    return None


def lay_nguoi_lien_he_neu_duoc_xem(nguoi_lien_he_id, nguoi_dung):
    """Lấy người liên hệ và kiểm tra quyền thông qua khách hàng họ đang thuộc về."""
    db = ket_noi_csdl()
    nlh = db.execute(
        "SELECT * FROM nguoi_lien_he WHERE id = ?", (nguoi_lien_he_id,)
    ).fetchone()
    if nlh is None:
        return None, (
            jsonify({
                "thanh_cong": False,
                "thong_bao": f"Không tìm thấy người liên hệ có id = {nguoi_lien_he_id}.",
            }),
            404,
        )
    _, loi = lay_khach_hang_neu_duoc_xem(nlh["khach_hang_id"], nguoi_dung)
    if loi:
        return None, loi
    return nlh, None


@api_nguoi_lien_he.post("/api/khach-hang/<int:khach_hang_id>/nguoi-lien-he")
def them_nguoi_lien_he(khach_hang_id):
    """[Tiêu chí 1+2+3] Thêm người liên hệ cho khách hàng."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    khach_hang, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True)
    if du_lieu is None:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Dữ liệu gửi lên phải ở dạng JSON. Ví dụ: {\"ho_ten\": \"Nguyễn Văn A\"}.",
        }), 400

    ho_ten = str(du_lieu.get("ho_ten") or "").strip()
    if not ho_ten:
        return jsonify({"thanh_cong": False, "thong_bao": "Thiếu họ tên người liên hệ."}), 400

    email = str(du_lieu.get("email") or "").strip()
    so_dien_thoai = str(du_lieu.get("so_dien_thoai") or "").strip()
    vai_tro_mua = str(du_lieu.get("vai_tro_mua") or "").strip() or None
    loi_kiem_tra = kiem_tra_thong_tin_lien_he(email, so_dien_thoai, vai_tro_mua)
    if loi_kiem_tra:
        return jsonify({"thanh_cong": False, "thong_bao": loi_kiem_tra}), 400

    db = ket_noi_csdl()
    la_dau_moi_chinh = 1 if du_lieu.get("la_dau_moi_chinh") else 0
    if la_dau_moi_chinh:
        # [Tiêu chí 3] Mỗi khách hàng chỉ có MỘT đầu mối chính
        db.execute(
            "UPDATE nguoi_lien_he SET la_dau_moi_chinh = 0 WHERE khach_hang_id = ?",
            (khach_hang_id,),
        )

    con_tro = db.execute(
        """INSERT INTO nguoi_lien_he
           (khach_hang_id, ho_ten, chuc_danh, email, so_dien_thoai, vai_tro_mua,
            la_dau_moi_chinh, ngay_tao)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            khach_hang_id, ho_ten,
            str(du_lieu.get("chuc_danh") or "").strip(),
            email, so_dien_thoai, vai_tro_mua, la_dau_moi_chinh, bay_gio(),
        ),
    )
    nguoi_lien_he_id = con_tro.lastrowid

    # [Tiêu chí 4] Mở lịch sử công ty đầu tiên của người liên hệ
    db.execute(
        """INSERT INTO lich_su_nguoi_lien_he
           (nguoi_lien_he_id, khach_hang_id, ten_cong_ty, tu_ngay, den_ngay)
           VALUES (?, ?, ?, ?, NULL)""",
        (nguoi_lien_he_id, khach_hang_id, khach_hang["ten_cong_ty"], bay_gio()),
    )
    ghi_hoat_dong(db, khach_hang_id, "Hệ thống",
                  f"Thêm người liên hệ '{ho_ten}'" + (f" (vai trò: {vai_tro_mua})" if vai_tro_mua else "") + ".",
                  nguoi_dung["id"])
    db.commit()

    return jsonify({
        "thanh_cong": True,
        "thong_bao": f"Đã thêm người liên hệ '{ho_ten}' cho khách hàng '{khach_hang['ten_cong_ty']}'.",
        "nguoi_lien_he_id": nguoi_lien_he_id,
    }), 201


@api_nguoi_lien_he.get("/api/khach-hang/<int:khach_hang_id>/nguoi-lien-he")
def danh_sach_nguoi_lien_he(khach_hang_id):
    """[Tiêu chí 1] Danh sách người liên hệ của một khách hàng."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    _, loi = lay_khach_hang_neu_duoc_xem(khach_hang_id, nguoi_dung)
    if loi:
        return loi

    db = ket_noi_csdl()
    danh_sach = db.execute(
        """SELECT * FROM nguoi_lien_he WHERE khach_hang_id = ?
           ORDER BY la_dau_moi_chinh DESC, id""",
        (khach_hang_id,),
    ).fetchall()
    return jsonify({
        "thanh_cong": True,
        "tong_so": len(danh_sach),
        "danh_sach": [chuyen_nlh_thanh_json(n) for n in danh_sach],
    })


@api_nguoi_lien_he.put("/api/nguoi-lien-he/<int:nguoi_lien_he_id>")
def cap_nhat_nguoi_lien_he(nguoi_lien_he_id):
    """[Tiêu chí 1+2] Cập nhật thông tin và vai trò trong quyết định mua."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    nlh, loi = lay_nguoi_lien_he_neu_duoc_xem(nguoi_lien_he_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True)
    if not du_lieu:
        return jsonify({"thanh_cong": False, "thong_bao": "Không có dữ liệu JSON nào để cập nhật."}), 400

    cap_nhat = {}
    if "ho_ten" in du_lieu:
        ho_ten_moi = str(du_lieu["ho_ten"]).strip()
        if not ho_ten_moi:
            return jsonify({"thanh_cong": False, "thong_bao": "Họ tên không được để trống."}), 400
        cap_nhat["ho_ten"] = ho_ten_moi
    if "chuc_danh" in du_lieu:
        cap_nhat["chuc_danh"] = str(du_lieu["chuc_danh"] or "").strip()

    email = str(du_lieu.get("email") or "").strip() if "email" in du_lieu else nlh["email"]
    sdt = str(du_lieu.get("so_dien_thoai") or "").strip() if "so_dien_thoai" in du_lieu else nlh["so_dien_thoai"]
    vai_tro_mua = (
        (str(du_lieu.get("vai_tro_mua") or "").strip() or None)
        if "vai_tro_mua" in du_lieu else nlh["vai_tro_mua"]
    )
    loi_kiem_tra = kiem_tra_thong_tin_lien_he(email, sdt, vai_tro_mua)
    if loi_kiem_tra:
        return jsonify({"thanh_cong": False, "thong_bao": loi_kiem_tra}), 400
    if "email" in du_lieu:
        cap_nhat["email"] = email
    if "so_dien_thoai" in du_lieu:
        cap_nhat["so_dien_thoai"] = sdt
    if "vai_tro_mua" in du_lieu:
        cap_nhat["vai_tro_mua"] = vai_tro_mua

    if not cap_nhat:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": (
                "Không có trường hợp lệ nào để cập nhật. Các trường được hỗ trợ: "
                "ho_ten, chuc_danh, email, so_dien_thoai, vai_tro_mua."
            ),
        }), 400

    db = ket_noi_csdl()
    cau_lenh = ", ".join(f"{ten} = ?" for ten in cap_nhat)
    db.execute(
        f"UPDATE nguoi_lien_he SET {cau_lenh} WHERE id = ?",
        (*cap_nhat.values(), nguoi_lien_he_id),
    )
    if "vai_tro_mua" in cap_nhat:
        ghi_hoat_dong(db, nlh["khach_hang_id"], "Hệ thống",
                      f"Cập nhật vai trò quyết định mua của '{nlh['ho_ten']}' thành '{cap_nhat['vai_tro_mua'] or 'chưa xác định'}'.",
                      nguoi_dung["id"])
    db.commit()

    nlh_moi = db.execute("SELECT * FROM nguoi_lien_he WHERE id = ?", (nguoi_lien_he_id,)).fetchone()
    return jsonify({
        "thanh_cong": True,
        "thong_bao": "Cập nhật người liên hệ thành công. Các trường đã thay đổi: " + ", ".join(cap_nhat.keys()) + ".",
        "nguoi_lien_he": chuyen_nlh_thanh_json(nlh_moi),
    })


@api_nguoi_lien_he.put("/api/nguoi-lien-he/<int:nguoi_lien_he_id>/dau-moi-chinh")
def dat_dau_moi_chinh(nguoi_lien_he_id):
    """[Tiêu chí 3] Đánh dấu người này là ĐẦU MỐI CHÍNH (tự bỏ đánh dấu người cũ)."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    nlh, loi = lay_nguoi_lien_he_neu_duoc_xem(nguoi_lien_he_id, nguoi_dung)
    if loi:
        return loi

    db = ket_noi_csdl()
    db.execute(
        "UPDATE nguoi_lien_he SET la_dau_moi_chinh = 0 WHERE khach_hang_id = ?",
        (nlh["khach_hang_id"],),
    )
    db.execute(
        "UPDATE nguoi_lien_he SET la_dau_moi_chinh = 1 WHERE id = ?",
        (nguoi_lien_he_id,),
    )
    ghi_hoat_dong(db, nlh["khach_hang_id"], "Hệ thống",
                  f"Đặt '{nlh['ho_ten']}' làm đầu mối chính.", nguoi_dung["id"])
    db.commit()
    return jsonify({
        "thanh_cong": True,
        "thong_bao": f"Đã đặt '{nlh['ho_ten']}' làm đầu mối chính của khách hàng này.",
    })


@api_nguoi_lien_he.put("/api/nguoi-lien-he/<int:nguoi_lien_he_id>/chuyen-cong-ty")
def chuyen_cong_ty(nguoi_lien_he_id):
    """
    [Tiêu chí 4] Người liên hệ chuyển sang công ty khác:
    - Gắn lại sang khách hàng mới.
    - GIỮ NGUYÊN lịch sử các công ty đã thuộc về (đóng giai đoạn cũ, mở giai đoạn mới).
    """
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    nlh, loi = lay_nguoi_lien_he_neu_duoc_xem(nguoi_lien_he_id, nguoi_dung)
    if loi:
        return loi

    du_lieu = request.get_json(silent=True) or {}
    khach_hang_moi_id = du_lieu.get("khach_hang_moi_id")
    if not khach_hang_moi_id:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Thiếu 'khach_hang_moi_id' - id của khách hàng (công ty) mới mà người này chuyển sang.",
        }), 400

    khach_hang_moi, loi = lay_khach_hang_neu_duoc_xem(int(khach_hang_moi_id), nguoi_dung)
    if loi:
        return loi
    if khach_hang_moi["id"] == nlh["khach_hang_id"]:
        return jsonify({
            "thanh_cong": False,
            "thong_bao": "Người liên hệ đang thuộc chính khách hàng này rồi, không cần chuyển.",
        }), 400

    db = ket_noi_csdl()
    luc_nay = bay_gio()

    # Đóng giai đoạn ở công ty cũ (giữ nguyên bản ghi -> lịch sử không mất)
    db.execute(
        """UPDATE lich_su_nguoi_lien_he SET den_ngay = ?
           WHERE nguoi_lien_he_id = ? AND den_ngay IS NULL""",
        (luc_nay, nguoi_lien_he_id),
    )
    # Mở giai đoạn ở công ty mới
    db.execute(
        """INSERT INTO lich_su_nguoi_lien_he
           (nguoi_lien_he_id, khach_hang_id, ten_cong_ty, tu_ngay, den_ngay)
           VALUES (?, ?, ?, ?, NULL)""",
        (nguoi_lien_he_id, khach_hang_moi["id"], khach_hang_moi["ten_cong_ty"], luc_nay),
    )
    # Gắn người liên hệ sang khách hàng mới (thôi làm đầu mối chính ở công ty mới cho an toàn)
    khach_hang_cu_id = nlh["khach_hang_id"]
    db.execute(
        "UPDATE nguoi_lien_he SET khach_hang_id = ?, la_dau_moi_chinh = 0 WHERE id = ?",
        (khach_hang_moi["id"], nguoi_lien_he_id),
    )
    ghi_hoat_dong(db, khach_hang_cu_id, "Hệ thống",
                  f"Người liên hệ '{nlh['ho_ten']}' đã chuyển sang công ty '{khach_hang_moi['ten_cong_ty']}'.",
                  nguoi_dung["id"])
    ghi_hoat_dong(db, khach_hang_moi["id"], "Hệ thống",
                  f"Tiếp nhận người liên hệ '{nlh['ho_ten']}' chuyển đến từ công ty cũ.",
                  nguoi_dung["id"])
    db.commit()

    return jsonify({
        "thanh_cong": True,
        "thong_bao": (
            f"Đã chuyển '{nlh['ho_ten']}' sang khách hàng '{khach_hang_moi['ten_cong_ty']}'. "
            "Lịch sử các công ty trước đây vẫn được giữ nguyên."
        ),
        "xem_lich_su": f"GET /api/nguoi-lien-he/{nguoi_lien_he_id}/lich-su",
    })


@api_nguoi_lien_he.get("/api/nguoi-lien-he/<int:nguoi_lien_he_id>/lich-su")
def lich_su_cong_ty(nguoi_lien_he_id):
    """[Tiêu chí 4] Xem lịch sử các công ty mà người liên hệ đã/đang thuộc về."""
    nguoi_dung, loi = lay_nguoi_dung_hien_tai()
    if loi:
        return loi
    nlh, loi = lay_nguoi_lien_he_neu_duoc_xem(nguoi_lien_he_id, nguoi_dung)
    if loi:
        return loi

    db = ket_noi_csdl()
    lich_su = db.execute(
        """SELECT * FROM lich_su_nguoi_lien_he
           WHERE nguoi_lien_he_id = ? ORDER BY tu_ngay""",
        (nguoi_lien_he_id,),
    ).fetchall()
    return jsonify({
        "thanh_cong": True,
        "nguoi_lien_he": nlh["ho_ten"],
        "tong_so_giai_doan": len(lich_su),
        "lich_su": [
            {
                "khach_hang_id": d["khach_hang_id"],
                "ten_cong_ty": d["ten_cong_ty"],
                "tu_ngay": d["tu_ngay"],
                "den_ngay": d["den_ngay"] or "hiện tại",
            }
            for d in lich_su
        ],
    })
