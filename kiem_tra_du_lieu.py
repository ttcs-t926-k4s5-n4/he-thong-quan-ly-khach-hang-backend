# -*- coding: utf-8 -*-
"""
KIỂM TRA DỮ LIỆU TỆP EXCEL [SCRUM-36]
Đọc tệp Excel tải lên và kiểm tra hợp lệ TỪNG DÒNG, trả về lỗi cụ thể theo dòng.
"""
import re

import openpyxl

from cau_hinh import CAC_VAI_TRO_HOP_LE, MAU_EMAIL, MAU_SDT_VIET_NAM
from co_so_du_lieu import ket_noi_csdl


def doc_va_kiem_tra_tep_excel(tep):
    """
    Trả về (danh_sach_ket_qua, loi_chung).
    Mỗi phần tử của danh_sach_ket_qua:
        {dong, du_lieu, hop_le, danh_sach_loi}
    """
    ten_tep = (tep.filename or "").lower()
    if not ten_tep.endswith((".xlsx", ".xlsm")):
        return None, "Tệp không hợp lệ. Vui lòng tải lên tệp Excel định dạng .xlsx (hãy dùng tệp mẫu của hệ thống)."

    try:
        so = openpyxl.load_workbook(tep, data_only=True)
    except Exception:
        return None, "Không đọc được tệp Excel. Tệp có thể bị hỏng hoặc sai định dạng."

    trang = so.worksheets[0]
    cac_dong = list(trang.iter_rows(min_row=2, values_only=True))
    if not cac_dong:
        return None, "Tệp không có dữ liệu (chỉ có dòng tiêu đề hoặc trống)."

    db = ket_noi_csdl()
    email_da_co = {
        d["email"].strip().lower()
        for d in db.execute("SELECT email FROM nguoi_dung").fetchall()
    }
    email_trong_tep = set()

    ket_qua = []
    for chi_so, dong in enumerate(cac_dong, start=2):  # dòng 2 trở đi trong Excel
        # Bỏ qua dòng hoàn toàn trống
        if dong is None or all(o is None or str(o).strip() == "" for o in dong):
            continue

        # Lấy giá trị theo đúng thứ tự cột của tệp mẫu
        gia_tri = list(dong) + [None] * (6 - len(dong))
        ho_ten = str(gia_tri[0]).strip() if gia_tri[0] is not None else ""
        email = str(gia_tri[1]).strip() if gia_tri[1] is not None else ""
        sdt = str(gia_tri[2]).strip() if gia_tri[2] is not None else ""
        nhom = str(gia_tri[3]).strip() if gia_tri[3] is not None else ""
        vai_tro = str(gia_tri[4]).strip() if gia_tri[4] is not None else ""
        mat_khau = str(gia_tri[5]).strip() if gia_tri[5] is not None else ""

        # Số điện thoại đọc từ Excel có thể bị mất số 0 đầu hoặc thành số thực
        if sdt.endswith(".0"):
            sdt = sdt[:-2]
        if sdt and re.fullmatch(r"[0-9]{9}", sdt):
            sdt = "0" + sdt

        danh_sach_loi = []

        # --- Kiểm tra họ tên ---
        if not ho_ten:
            danh_sach_loi.append("Thiếu họ và tên.")

        # --- Kiểm tra email ---
        if not email:
            danh_sach_loi.append("Thiếu email.")
        elif not MAU_EMAIL.fullmatch(email):
            danh_sach_loi.append(f"Email '{email}' sai định dạng.")
        else:
            email_chuan = email.lower()
            if email_chuan in email_da_co:
                danh_sach_loi.append(f"Email '{email}' đã tồn tại trong hệ thống.")
            elif email_chuan in email_trong_tep:
                danh_sach_loi.append(f"Email '{email}' bị trùng với một dòng khác trong tệp.")
            else:
                email_trong_tep.add(email_chuan)

        # --- Kiểm tra số điện thoại Việt Nam (nếu có điền) ---
        if sdt and not MAU_SDT_VIET_NAM.fullmatch(sdt):
            danh_sach_loi.append(
                f"Số điện thoại '{sdt}' không đúng định dạng Việt Nam (bắt đầu bằng 0 hoặc +84, ví dụ 0912345678)."
            )

        # --- Kiểm tra vai trò ---
        if not vai_tro:
            danh_sach_loi.append("Thiếu vai trò.")
        elif vai_tro not in CAC_VAI_TRO_HOP_LE:
            danh_sach_loi.append(
                f"Vai trò '{vai_tro}' không hợp lệ. Chỉ chấp nhận: {', '.join(CAC_VAI_TRO_HOP_LE)}."
            )

        ket_qua.append({
            "dong": chi_so,
            "du_lieu": {
                "ho_ten": ho_ten,
                "email": email,
                "so_dien_thoai": sdt,
                "nhom": nhom,
                "vai_tro": vai_tro,
                "mat_khau": mat_khau,
            },
            "hop_le": len(danh_sach_loi) == 0,
            "danh_sach_loi": danh_sach_loi,
        })

    if not ket_qua:
        return None, "Tệp không có dòng dữ liệu nào."
    return ket_qua, None
