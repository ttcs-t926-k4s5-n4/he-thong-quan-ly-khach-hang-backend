# -*- coding: utf-8 -*-
"""
KIỂM THỬ TỰ ĐỘNG TOÀN BỘ TIÊU CHÍ CỦA 3 CHỨC NĂNG (SCRUM-69 / 70 / 71)
Chạy:  python kiem_thu.py
(Lưu ý: file này xóa crm_khach_hang.db cũ để kiểm thử trên dữ liệu sạch.)
"""
import io
import os
import sqlite3
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists("crm_khach_hang.db"):
    os.remove("crm_khach_hang.db")

from co_so_du_lieu import khoi_tao_csdl
from cau_hinh import TEP_CSDL
from main import app

khoi_tao_csdl()
client = app.test_client()

QUAN_TRI = {"X-User-Id": "1"}
TRUONG_NHOM = {"X-User-Id": "2"}   # Nhóm kinh doanh 1
NHAN_VIEN_A = {"X-User-Id": "3"}   # Nhóm kinh doanh 1
NHAN_VIEN_B = {"X-User-Id": "4"}   # Nhóm kinh doanh 2


def kiem(ten, dieu_kien):
    print(("[ĐẠT] " if dieu_kien else "[LỖI] ") + ten)
    assert dieu_kien, ten


# ============================= SCRUM-69 =============================
print("----- SCRUM-69: Hồ sơ khách hàng doanh nghiệp -----")
r = client.post("/api/khach-hang", headers=NHAN_VIEN_A, json={
    "ten_cong_ty": "Công ty TNHH Alpha",
    "ma_so_thue": "0101243150",
    "nganh_nghe": "Phần mềm",
    "quy_mo": "50-100 nhân sự",
    "website": "https://alpha.vn",
    "dia_chi": "Hà Nội",
})
kiem("69.1 Khai báo đủ trường (tên, MST, ngành nghề, quy mô, website, địa chỉ, người sở hữu)",
     r.status_code == 201)
kh_a = r.get_json()["khach_hang_id"]

r = client.post("/api/khach-hang", headers=NHAN_VIEN_B, json={
    "ten_cong_ty": "Công ty CP Beta", "ma_so_thue": "0101243150",
})
kiem("69.2 Mã số thuế trùng bị từ chối (MST phải duy nhất)", r.status_code == 400)
print("   ->", r.get_json()["thong_bao"])
r = client.post("/api/khach-hang", headers=NHAN_VIEN_B, json={
    "ten_cong_ty": "Công ty CP Beta", "ma_so_thue": "abc123",
})
kiem("69.2 MST sai định dạng bị từ chối", r.status_code == 400)
r = client.post("/api/khach-hang", headers=NHAN_VIEN_B, json={
    "ten_cong_ty": "Công ty CP Beta", "ma_so_thue": "0312345678",
})
kiem("69.2 MST khác (hợp lệ) được chấp nhận", r.status_code == 201)
kh_b = r.get_json()["khach_hang_id"]
r = client.post("/api/khach-hang", headers=NHAN_VIEN_A, json={"ten_cong_ty": "Công ty không MST"})
kiem("69.2 Không có MST vẫn tạo được (MST là tùy chọn)", r.status_code == 201)

r = client.post("/api/khach-hang", headers=NHAN_VIEN_A, json={
    "ten_cong_ty": "Thử trạng thái", "trang_thai": "Đã phá sản",
})
kiem("69.3 Trạng thái ngoài 4 giá trị bị từ chối", r.status_code == 400)
r = client.put(f"/api/khach-hang/{kh_a}", headers=NHAN_VIEN_A, json={"trang_thai": "Đang giao dịch"})
kiem("69.3 Chuyển trạng thái hợp lệ (Tiềm năng -> Đang giao dịch)",
     r.status_code == 200 and r.get_json()["khach_hang"]["trang_thai"] == "Đang giao dịch")

r = client.get("/api/khach-hang", headers=NHAN_VIEN_A)
j = r.get_json()
kiem("69.4 Nhân viên A chỉ thấy khách hàng MÌNH sở hữu",
     all(kh["nguoi_so_huu"]["id"] == 3 for kh in j["danh_sach"]) and j["tong_so"] == 2)
r = client.get(f"/api/khach-hang/{kh_a}", headers=NHAN_VIEN_B)
kiem("69.4 Nhân viên B (khác nhóm) bị chặn xem khách hàng của A (403)", r.status_code == 403)
print("   ->", r.get_json()["thong_bao"])
r = client.get(f"/api/khach-hang/{kh_a}", headers=TRUONG_NHOM)
kiem("69.4 Trưởng nhóm (Nhóm KD 1) xem được khách hàng của A (cùng nhóm)", r.status_code == 200)
r = client.get(f"/api/khach-hang/{kh_b}", headers=TRUONG_NHOM)
kiem("69.4 Trưởng nhóm KHÔNG xem được khách hàng của B (khác nhóm)", r.status_code == 403)
r = client.get("/api/khach-hang", headers=QUAN_TRI)
kiem("69.4 Quản trị hệ thống thấy tất cả", r.get_json()["tong_so"] == 3)

# ============================= SCRUM-70 =============================
print("----- SCRUM-70: Người liên hệ & vai trò quyết định mua -----")
r = client.post(f"/api/khach-hang/{kh_a}/nguoi-lien-he", headers=NHAN_VIEN_A, json={
    "ho_ten": "Nguyễn Văn Giám Đốc", "chuc_danh": "Giám đốc",
    "email": "giamdoc@alpha.vn", "so_dien_thoai": "0912345678",
    "vai_tro_mua": "Người quyết định", "la_dau_moi_chinh": True,
})
kiem("70.1 Thêm người liên hệ có chức danh, email, SĐT", r.status_code == 201)
nlh_1 = r.get_json()["nguoi_lien_he_id"]
r = client.post(f"/api/khach-hang/{kh_a}/nguoi-lien-he", headers=NHAN_VIEN_A, json={
    "ho_ten": "Trần Thị Kế Toán", "chuc_danh": "Kế toán trưởng",
    "email": "ketoan@alpha.vn", "so_dien_thoai": "0987654321",
    "vai_tro_mua": "Người cản trở",
})
nlh_2 = r.get_json()["nguoi_lien_he_id"]
r = client.get(f"/api/khach-hang/{kh_a}/nguoi-lien-he", headers=NHAN_VIEN_A)
kiem("70.1 Một khách hàng có NHIỀU người liên hệ", r.get_json()["tong_so"] == 2)

r = client.post(f"/api/khach-hang/{kh_a}/nguoi-lien-he", headers=NHAN_VIEN_A, json={
    "ho_ten": "Người Sai Vai Trò", "vai_tro_mua": "Người xem chơi",
})
kiem("70.2 Vai trò mua ngoài 4 giá trị bị từ chối", r.status_code == 400)
print("   ->", r.get_json()["thong_bao"])
r = client.put(f"/api/nguoi-lien-he/{nlh_2}", headers=NHAN_VIEN_A,
               json={"vai_tro_mua": "Người ảnh hưởng"})
kiem("70.2 Cập nhật vai trò mua hợp lệ (Người cản trở -> Người ảnh hưởng)",
     r.status_code == 200 and r.get_json()["nguoi_lien_he"]["vai_tro_mua"] == "Người ảnh hưởng")

r = client.put(f"/api/nguoi-lien-he/{nlh_2}/dau-moi-chinh", headers=NHAN_VIEN_A)
kiem("70.3 Đặt đầu mối chính thành công", r.status_code == 200)
r = client.get(f"/api/khach-hang/{kh_a}/nguoi-lien-he", headers=NHAN_VIEN_A)
ds = r.get_json()["danh_sach"]
kiem("70.3 Chỉ có đúng MỘT đầu mối chính (người cũ tự bị bỏ đánh dấu)",
     sum(1 for n in ds if n["la_dau_moi_chinh"]) == 1
     and next(n for n in ds if n["la_dau_moi_chinh"])["id"] == nlh_2)

# Chuyển công ty: tạo thêm khách hàng thứ hai của A để chuyển hợp lệ
r = client.post("/api/khach-hang", headers=NHAN_VIEN_A, json={"ten_cong_ty": "Công ty TNHH Gamma"})
kh_gamma = r.get_json()["khach_hang_id"]
r = client.put(f"/api/nguoi-lien-he/{nlh_1}/chuyen-cong-ty", headers=NHAN_VIEN_A,
               json={"khach_hang_moi_id": kh_gamma})
kiem("70.4 Chuyển người liên hệ sang công ty khác thành công", r.status_code == 200)
r = client.get(f"/api/nguoi-lien-he/{nlh_1}/lich-su", headers=NHAN_VIEN_A)
j = r.get_json()
kiem("70.4 Lịch sử GIỮ NGUYÊN: 2 giai đoạn (Alpha -> Gamma), giai đoạn cũ có ngày kết thúc",
     j["tong_so_giai_doan"] == 2
     and j["lich_su"][0]["ten_cong_ty"] == "Công ty TNHH Alpha"
     and j["lich_su"][0]["den_ngay"] != "hiện tại"
     and j["lich_su"][1]["ten_cong_ty"] == "Công ty TNHH Gamma"
     and j["lich_su"][1]["den_ngay"] == "hiện tại")
r = client.get(f"/api/khach-hang/{kh_gamma}/nguoi-lien-he", headers=NHAN_VIEN_A)
kiem("70.4 Người liên hệ đã gắn sang khách hàng mới",
     any(n["id"] == nlh_1 for n in r.get_json()["danh_sach"]))

# ============================= SCRUM-71 =============================
print("----- SCRUM-71: Trang 360 của khách hàng -----")
client.post(f"/api/khach-hang/{kh_a}/co-hoi", headers=NHAN_VIEN_A,
            json={"ten_co_hoi": "Hợp đồng CRM giai đoạn 1", "gia_tri": 500000000, "trang_thai": "Đã thắng"})
client.post(f"/api/khach-hang/{kh_a}/co-hoi", headers=NHAN_VIEN_A,
            json={"ten_co_hoi": "Hợp đồng bảo trì", "gia_tri": 120000000, "trang_thai": "Đã thắng"})
client.post(f"/api/khach-hang/{kh_a}/co-hoi", headers=NHAN_VIEN_A,
            json={"ten_co_hoi": "Mở rộng giai đoạn 2", "gia_tri": 800000000, "trang_thai": "Đang mở"})
client.post(f"/api/khach-hang/{kh_a}/co-hoi", headers=NHAN_VIEN_A,
            json={"ten_co_hoi": "Gói đào tạo", "gia_tri": 90000000, "trang_thai": "Đã thua"})
client.post(f"/api/khach-hang/{kh_a}/hoat-dong", headers=NHAN_VIEN_A,
            json={"loai": "Cuộc gọi", "noi_dung": "Gọi điện chốt lịch demo sản phẩm."})
r = client.post(f"/api/khach-hang/{kh_a}/tep-dinh-kem", headers=NHAN_VIEN_A,
                data={"tep": (io.BytesIO("Nội dung báo giá thử nghiệm".encode("utf-8")), "bao_gia.txt")},
                content_type="multipart/form-data")
kiem("71.x Tải tệp đính kèm thành công", r.status_code == 201)

# Bơm cho đủ 500 hoạt động (ghi thẳng vào CSDL cho nhanh)
ket_noi = sqlite3.connect(TEP_CSDL)
goc = datetime.now()
so_hien_co = ket_noi.execute(
    "SELECT COUNT(*) FROM hoat_dong WHERE khach_hang_id = ?", (kh_a,)
).fetchone()[0]
ket_noi.executemany(
    """INSERT INTO hoat_dong (khach_hang_id, loai, noi_dung, nguoi_thuc_hien_id, thoi_gian)
       VALUES (?, ?, ?, ?, ?)""",
    [
        (kh_a, "Email", f"Trao đổi email số {i} với khách hàng.", 3,
         (goc - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"))
        for i in range(500 - so_hien_co)
    ],
)
ket_noi.commit()
ket_noi.close()

r = client.get(f"/api/khach-hang/{kh_a}/trang-360", headers=NHAN_VIEN_A)
j = r.get_json()
t360 = j["trang_360"]
kiem("71.1 Trang 360 gom đủ 5 khối: công ty, người liên hệ, cơ hội, dòng thời gian, tệp",
     r.status_code == 200
     and t360["thong_tin_cong_ty"]["ten_cong_ty"] == "Công ty TNHH Alpha"
     and t360["nguoi_lien_he"]["tong_so"] >= 1
     and len(t360["co_hoi"]["dang_mo"]) == 1 and len(t360["co_hoi"]["da_dong"]) == 3
     and t360["dong_thoi_gian"]["tong_so_hoat_dong"] == 500
     and t360["tep_dinh_kem"]["tong_so"] == 1)
kiem("71.2 Tổng giá trị ĐÃ KÝ đúng (500tr + 120tr = 620.000.000)",
     t360["co_hoi"]["tong_gia_tri_da_ky"] == 620000000)
kiem("71.2 Giá trị cơ hội ĐANG MỞ đúng (800.000.000)",
     t360["co_hoi"]["tong_gia_tri_dang_mo"] == 800000000)
kiem(f"71.3 Tải 500 hoạt động dưới 1,5 giây (thực tế: {j['hieu_nang']['thoi_gian_tai_giay']}s)",
     j["hieu_nang"]["dat_tieu_chi_duoi_1_5_giay"]
     and t360["dong_thoi_gian"]["so_hoat_dong_tra_ve"] == 500)
r = client.get(f"/api/khach-hang/{kh_a}/trang-360", headers=NHAN_VIEN_B)
kiem("71.x Trang 360 cũng được bảo vệ bởi phân quyền (B bị chặn 403)", r.status_code == 403)

print("\n>>> TẤT CẢ KIỂM THỬ ĐỀU ĐẠT - SẴN SÀNG BÀN GIAO <<<")
