# Backend CRM - 3 chức năng (SCRUM-36, SCRUM-60, SCRUM-61)

Backend viết bằng **Python + Flask + SQLite**, toàn bộ thông báo bằng **tiếng Việt**.

## Cấu trúc project

| File | Vai trò |
|---|---|
| `main.py` | File chạy chính: tạo app, đăng ký 3 chức năng, trang chủ, xử lý lỗi |
| `cau_hinh.py` | Hằng số, đường dẫn, biểu thức kiểm tra (SĐT Việt Nam, email) |
| `co_so_du_lieu.py` | SQLite: tạo bảng, dữ liệu mẫu, băm mật khẩu |
| `xac_thuc.py` | Xác thực demo qua header `X-User-Id` |
| `kiem_tra_du_lieu.py` | Kiểm tra hợp lệ từng dòng tệp Excel (SCRUM-36) |
| `api_nguoi_dung.py` | **[SCRUM-36]** Nhập người dùng hàng loạt từ Excel |
| `api_ho_so.py` | **[SCRUM-60]** Xem / cập nhật hồ sơ cá nhân |
| `api_anh_dai_dien.py` | **[SCRUM-61]** Tải lên ảnh đại diện |
| `kiem_thu.py` | Kiểm thử tự động toàn bộ tiêu chí |

## Cách chạy (trong VS Code)

Mở terminal tại thư mục project rồi chạy:

```bash
pip install -r requirements.txt
python main.py
```

Server chạy tại: **http://127.0.0.1:5000** — mở trên trình duyệt để xem danh sách API.

Chạy kiểm thử tự động:

```bash
python kiem_thu.py
```

## Xác thực (demo)

Thêm header `X-User-Id` vào request (dùng Postman):
- `X-User-Id: 1` → Nguyễn Quản Trị (Quản trị hệ thống, mật khẩu `admin123`)
- `X-User-Id: 2` → Trần Văn Nhân Viên (Nhân viên kinh doanh, mật khẩu `123456`)

CSDL `crm.db` và thư mục `anh_dai_dien/` tự tạo khi chạy lần đầu.

## Danh sách API theo tiêu chí Jira

### SCRUM-36 — Nhập người dùng hàng loạt từ Excel
| Tiêu chí | API |
|---|---|
| Tải được tệp mẫu | `GET /api/nguoi-dung/tep-mau` |
| Xem trước và báo lỗi theo từng dòng trước khi nhập | `POST /api/nguoi-dung/xem-truoc` (form-data: `tep` = file .xlsx) |
| Dòng lỗi bị bỏ qua, dòng hợp lệ vẫn được nhập, có báo cáo tổng kết | `POST /api/nguoi-dung/nhap-hang-loat` (form-data: `tep` = file .xlsx) |
| (Kiểm tra kết quả) | `GET /api/nguoi-dung` |

### SCRUM-60 — Hồ sơ cá nhân
| Tiêu chí | API |
|---|---|
| Sửa được họ tên, số điện thoại, chữ ký email | `GET /api/ho-so`, `PUT /api/ho-so` (JSON: `ho_ten`, `so_dien_thoai`, `chu_ky_email`) |
| Không tự đổi được email, nhóm và vai trò | Gửi `email`/`nhom`/`vai_tro` → bị chặn **403** |
| Kiểm tra định dạng số điện thoại Việt Nam | Chỉ nhận `0xxx` hoặc `+84xxx` đúng đầu số nhà mạng |

### SCRUM-61 — Ảnh đại diện
| Tiêu chí | API |
|---|---|
| Chấp nhận JPG/PNG tối đa 2MB | `POST /api/ho-so/anh-dai-dien` (form-data: `anh` = file ảnh) |
| Ảnh được cắt vuông và tạo bản thu nhỏ | Tự cắt vuông giữa ảnh → 512×512 + thumbnail 128×128; xem lại: `GET /api/ho-so/anh-dai-dien`, `GET /api/ho-so/anh-thu-nho` |
