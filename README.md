# Backend CRM Khách hàng - 3 chức năng (SCRUM-69, SCRUM-70, SCRUM-71)

Backend viết bằng **Python + Flask + SQLite**, toàn bộ thông báo bằng **tiếng Việt**.
Mỗi SCRUM nằm trong **một file riêng** để commit lên một nhánh `feature/...` riêng.

## Cấu trúc project

| File | SCRUM | Vai trò |
|---|---|---|
| `main.py` | — | File chạy chính: tạo app, đăng ký 3 chức năng, trang chủ, xử lý lỗi |
| `cau_hinh.py` | — | Hằng số: 4 trạng thái KH, 4 vai trò mua, regex MST/SĐT/email |
| `co_so_du_lieu.py` | — | SQLite: 7 bảng, chỉ mục tăng tốc, 4 người dùng mẫu |
| `xac_thuc.py` | 69 | Xác thực + **phân quyền** nhân viên/trưởng nhóm/quản trị |
| `api_khach_hang.py` | **69** | Hồ sơ khách hàng doanh nghiệp |
| `api_nguoi_lien_he.py` | **70** | Người liên hệ & vai trò quyết định mua |
| `api_trang_360.py` | **71** | Trang 360 + cơ hội / hoạt động / tệp đính kèm |
| `kiem_thu.py` | — | Kiểm thử tự động toàn bộ tiêu chí (kể cả hiệu năng 500 hoạt động) |

## Cách chạy (trong VS Code)

Mở terminal **đúng thư mục chứa `main.py`** (chuột phải `main.py` → Open in Integrated Terminal):

```bash
pip install -r requirements.txt
python main.py
```

Server: **http://127.0.0.1:5000** — mở trên trình duyệt để xem danh sách API.

Chạy kiểm thử tự động:

```bash
python kiem_thu.py
```

## Xác thực (demo)

Gửi header `X-User-Id` **hoặc** thêm `?user_id=` vào URL (test nhanh trên trình duyệt):

| id | Người dùng | Vai trò | Nhóm |
|---|---|---|---|
| 1 | Nguyễn Quản Trị | Quản trị hệ thống | Ban điều hành |
| 2 | Lê Trưởng Nhóm | Trưởng nhóm | Nhóm kinh doanh 1 |
| 3 | Trần Nhân Viên A | Nhân viên kinh doanh | Nhóm kinh doanh 1 |
| 4 | Phạm Nhân Viên B | Nhân viên kinh doanh | Nhóm kinh doanh 2 |

Ví dụ test phân quyền ngay trên trình duyệt:
- `http://127.0.0.1:5000/api/khach-hang?user_id=3` → A chỉ thấy KH của mình
- `http://127.0.0.1:5000/api/khach-hang?user_id=2` → trưởng nhóm thấy cả nhóm 1
- `http://127.0.0.1:5000/api/khach-hang?user_id=1` → quản trị thấy tất cả

## Đối chiếu tiêu chí Jira ↔ API

### SCRUM-69 — Hồ sơ khách hàng doanh nghiệp
| Tiêu chí | API |
|---|---|
| Khai báo tên công ty, MST, ngành nghề, quy mô, website, địa chỉ, người sở hữu | `POST /api/khach-hang` |
| MST nếu có thì phải là duy nhất | kiểm tra khi tạo/sửa, trùng → lỗi 400 |
| 4 trạng thái: Tiềm năng, Đang giao dịch, Khách hàng, Ngừng hợp tác | trường `trang_thai`, `PUT /api/khach-hang/<id>` |
| Nhân viên chỉ thấy KH mình sở hữu; trưởng nhóm thấy toàn nhóm | `GET /api/khach-hang`, `GET /api/khach-hang/<id>` lọc theo quyền |

### SCRUM-70 — Người liên hệ & vai trò quyết định mua
| Tiêu chí | API |
|---|---|
| Mỗi KH nhiều người liên hệ (chức danh, email, SĐT) | `POST/GET /api/khach-hang/<id>/nguoi-lien-he` |
| Vai trò mua: quyết định / ảnh hưởng / dùng cuối / cản trở | trường `vai_tro_mua`, `PUT /api/nguoi-lien-he/<id>` |
| Đánh dấu một người là đầu mối chính | `PUT /api/nguoi-lien-he/<id>/dau-moi-chinh` (tự bỏ người cũ) |
| Chuyển sang công ty khác, giữ nguyên lịch sử | `PUT /api/nguoi-lien-he/<id>/chuyen-cong-ty` + `GET /api/nguoi-lien-he/<id>/lich-su` |

### SCRUM-71 — Trang 360 của khách hàng
| Tiêu chí | API |
|---|---|
| Một trang gom: công ty, người liên hệ, cơ hội mở/đóng, dòng thời gian, tệp đính kèm | `GET /api/khach-hang/<id>/trang-360` |
| Tổng giá trị đã ký và giá trị cơ hội đang mở | `tong_gia_tri_da_ky`, `tong_gia_tri_dang_mo` trong kết quả |
| Tải xong dưới 1,5 giây với 500 hoạt động | chỉ mục `(khach_hang_id, thoi_gian)`; kết quả trả kèm `thoi_gian_tai_giay` (thực đo ~0.002s) |

API tạo dữ liệu cho trang 360: `POST /api/khach-hang/<id>/co-hoi`, `POST .../hoat-dong`, `POST .../tep-dinh-kem` (form-data `tep`, ≤10MB), `GET /api/tep-dinh-kem/<id>`.

## Tạo nhánh feature trên GitHub (theo quy ước của nhóm)

Mỗi SCRUM một nhánh tách từ `develop`, đặt tên giống các nhánh có sẵn:

```bash
# Lấy code mới nhất của develop
git checkout develop
git pull origin develop

# ----- SCRUM-69 (kèm các file nền tảng dùng chung) -----
git checkout -b feature/SCRUM-69-customer-profiles-backend
git add main.py cau_hinh.py co_so_du_lieu.py xac_thuc.py api_khach_hang.py requirements.txt README.md
git commit -m "SCRUM-69: Quan ly ho so khach hang doanh nghiep (MST duy nhat, 4 trang thai, phan quyen xem)"
git push -u origin feature/SCRUM-69-customer-profiles-backend

# ----- SCRUM-70 -----
git checkout develop
git checkout -b feature/SCRUM-70-contacts-buying-roles-backend
git add api_nguoi_lien_he.py
git commit -m "SCRUM-70: Nguoi lien he va vai tro quyet dinh mua (dau moi chinh, chuyen cong ty giu lich su)"
git push -u origin feature/SCRUM-70-contacts-buying-roles-backend

# ----- SCRUM-71 -----
git checkout develop
git checkout -b feature/SCRUM-71-customer-360-backend
git add api_trang_360.py kiem_thu.py
git commit -m "SCRUM-71: Trang 360 khach hang (tong gia tri da ky/dang mo, tai 500 hoat dong duoi 1.5s)"
git push -u origin feature/SCRUM-71-customer-360-backend
```

Sau đó mở Pull Request từng nhánh vào `develop` trên GitHub.
Lưu ý: nhánh 70 và 71 phụ thuộc code nền ở nhánh 69, nên gộp (merge) nhánh 69 vào `develop` trước, hoặc tách nhánh 70/71 từ nhánh 69 nếu nhóm cho phép.
