# -*- coding: utf-8 -*-
"""
CẤU HÌNH CHUNG CỦA HỆ THỐNG
Hằng số, đường dẫn và biểu thức kiểm tra dùng chung cho cả 3 chức năng.
"""
import os
import re

# ----- Đường dẫn -----
DUONG_DAN_GOC = os.path.dirname(os.path.abspath(__file__))
TEP_CSDL = os.path.join(DUONG_DAN_GOC, "crm_khach_hang.db")
THU_MUC_TEP_DINH_KEM = os.path.join(DUONG_DAN_GOC, "tep_dinh_kem")

# ----- [SCRUM-69] Hồ sơ khách hàng doanh nghiệp -----
CAC_TRANG_THAI_KHACH_HANG = [
    "Tiềm năng",
    "Đang giao dịch",
    "Khách hàng",
    "Ngừng hợp tác",
]
TRANG_THAI_MAC_DINH = "Tiềm năng"

# ----- Vai trò người dùng hệ thống (phục vụ phân quyền) -----
VAI_TRO_QUAN_TRI = "Quản trị hệ thống"
VAI_TRO_TRUONG_NHOM = "Trưởng nhóm"
VAI_TRO_NHAN_VIEN = "Nhân viên kinh doanh"

# ----- [SCRUM-70] Vai trò trong quyết định mua -----
CAC_VAI_TRO_QUYET_DINH_MUA = [
    "Người quyết định",
    "Người ảnh hưởng",
    "Người dùng cuối",
    "Người cản trở",
]

# ----- [SCRUM-70] Trạng thái cơ hội (phục vụ trang 360) -----
CAC_TRANG_THAI_CO_HOI = ["Đang mở", "Đã thắng", "Đã thua"]

# ----- [SCRUM-71] Trang 360 -----
GIOI_HAN_HOAT_DONG_MAC_DINH = 500      # số hoạt động tải trong dòng thời gian
THOI_GIAN_TAI_TOI_DA_GIAY = 1.5        # tiêu chí: tải xong dưới 1,5 giây
KICH_THUOC_TEP_TOI_DA = 10 * 1024 * 1024  # tệp đính kèm tối đa 10MB

# ----- Biểu thức kiểm tra định dạng -----
MAU_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
# Số điện thoại Việt Nam: bắt đầu bằng 0 hoặc +84, đầu số 03x/05x/07x/08x/09x
MAU_SDT_VIET_NAM = re.compile(
    r"^(0|\+84)(3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}$"
)
# Mã số thuế Việt Nam: 10 chữ số, hoặc 10 chữ số + "-" + 3 chữ số (chi nhánh)
MAU_MA_SO_THUE = re.compile(r"^[0-9]{10}(-[0-9]{3})?$")
