# -*- coding: utf-8 -*-
"""
CẤU HÌNH CHUNG CỦA HỆ THỐNG
Chứa toàn bộ hằng số, đường dẫn và biểu thức kiểm tra dùng chung.
"""
import os
import re

# ----- Đường dẫn -----
DUONG_DAN_GOC = os.path.dirname(os.path.abspath(__file__))
TEP_CSDL = os.path.join(DUONG_DAN_GOC, "crm.db")
THU_MUC_ANH = os.path.join(DUONG_DAN_GOC, "anh_dai_dien")

# ----- [SCRUM-61] Ảnh đại diện -----
KICH_THUOC_ANH_TOI_DA = 2 * 1024 * 1024          # tối đa 2MB theo tiêu chí
DINH_DANG_ANH_CHO_PHEP = {".jpg", ".jpeg", ".png"}
KICH_THUOC_ANH_DAI_DIEN = 512                     # ảnh vuông 512x512
KICH_THUOC_ANH_THU_NHO = 128                      # bản thu nhỏ 128x128

# ----- [SCRUM-36] Nhập người dùng hàng loạt -----
CAC_VAI_TRO_HOP_LE = [
    "Quản trị hệ thống",
    "Giám đốc kinh doanh",
    "Trưởng nhóm",
    "Nhân viên kinh doanh",
]
MAT_KHAU_MAC_DINH = "123456"
CAC_COT_TEP_MAU = [
    "Họ và tên (*)", "Email (*)", "Số điện thoại", "Nhóm", "Vai trò (*)", "Mật khẩu",
]

# ----- [SCRUM-60] Kiểm tra định dạng -----
# Số điện thoại Việt Nam: bắt đầu bằng 0 hoặc +84, đầu số 03x/05x/07x/08x/09x
MAU_SDT_VIET_NAM = re.compile(
    r"^(0|\+84)(3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}$"
)
MAU_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
