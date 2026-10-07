# Hệ Thống Quản Lý Khách Hàng (CRM) – Backend API Service

> **Học phần:** Thực tập cơ sở  
> **Nhóm phát triển:** TTCS_T926_K4S5_N4  
> **Kiến trúc:** RESTful API Service (Python, Flask, SQLite)

---

## 1. Giới thiệu tổng quan

Hệ thống Backend cung cấp dịch vụ API phục vụ quản lý vòng đời khách hàng, theo dõi cơ hội bán hàng, đường ống giao dịch (Pipeline Kanban), sản phẩm/dịch vụ, hoạt động tương tác và điều phối công việc cho đội ngũ kinh doanh.

Mã nguồn được thiết kế theo cấu trúc module hoá (Modular Architecture), phân quyền truy cập dữ liệu chặt chẽ theo vai trò (RBAC), kèm bộ kiểm thử tự động với **73 test cases** bao phủ toàn bộ các quy tắc nghiệp vụ.

### Các phân hệ chính:
* **Quản lý Cơ hội bán hàng & Pipeline (Epic SCRUM-20):**
  * `SCRUM-87`: Khởi tạo và quản lý cơ hội bán hàng.
  * `SCRUM-88`: Bảng trực quan Pipeline dạng Kanban.
  * `SCRUM-89`: Quản lý danh mục sản phẩm, dịch vụ và hợp đồng thuê bao trong cơ hội.
  * `SCRUM-90`: Cấu hình ràng buộc giai đoạn (Stage Gates) và cơ chế ghi đè phê duyệt.
* **Tương tác Khách hàng & Điều phối Công việc (Epic SCRUM-21):**
  * `SCRUM-99`: Ghi nhận nhật ký tương tác với khách hàng (cuộc gọi, cuộc gặp, email, ghi chú).
  * `SCRUM-100`: Quản lý, phân công và giám sát công việc có hạn hoàn thành (Tasks).

---

## 2. Công nghệ và Môi trường

* **Ngôn ngữ:** Python 3.10+
* **Framework:** Flask
* **Cơ sở dữ liệu:** SQLite3 (nhẹ, độc lập, không yêu cầu cài đặt máy chủ DB riêng)
* **Xác thực & Phân quyền:** Token-based Authentication, kiểm soát phạm vi dữ liệu theo vai trò (Role-Based Access Control)
* **Quy chuẩn dữ liệu:** Chuẩn hoá định dạng thời gian Việt Nam (ISO 8601 / DD-MM-YYYY), tìm kiếm tiếng Việt không dấu, phản hồi lỗi chuẩn RESTful.

---

## 3. Hướng dẫn cài đặt và Khởi chạy

### Cách 1: Khởi chạy tự động với PowerShell (Khuyên dùng)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\chay_server.ps1
```
*Script sẽ tự động kiểm tra môi trường, tạo virtual environment `.venv`, cài đặt thư viện và nạp dữ liệu mẫu ban đầu.*

Truy cập danh mục tra cứu tài liệu toàn bộ API tại:  
👉 `http://127.0.0.1:5000/api`

*(Nếu cần làm mới toàn bộ cơ sở dữ liệu mẫu: `.\chay_server.ps1 -TaoLaiDuLieu`)*

### Cách 2: Khởi chạy thủ công
```powershell
# 1. Khởi tạo và kích hoạt môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Cài đặt các gói phụ thuộc
pip install -r requirements.txt

# 3. Tạo cơ sở dữ liệu và nạp dữ liệu mẫu
python -m app.seed --reset

# 4. Chạy ứng dụng
python run.py
```

*Các tham số cấu hình tuỳ chọn qua biến môi trường:*
* `CRM_PORT`: Cổng dịch vụ (mặc định: `5000`).
* `CRM_DATABASE`: Đường dẫn file CSDL (mặc định: `instance/crm.sqlite3`).
* `CRM_TOKEN_MAX_AGE`: Thời hạn hiệu lực của token (giây, mặc định: 8 giờ).

---

## 4. Tài khoản thử nghiệm (Mật khẩu mặc định: `123456`)

Hệ thống được nạp sẵn dữ liệu kiểm thử thực tế đại diện cho cơ cấu tổ chức doanh nghiệp:

| Tên đăng nhập | Họ và tên | Vai trò | Phạm vi quản lý |
|---|---|---|---|
| `giamdoc` | Nguyễn Văn An | Giám đốc kinh doanh | Toàn bộ dữ liệu hệ thống |
| `truongnhom1` | Trần Thị Bình | Trưởng nhóm | Nhóm kinh doanh Miền Bắc |
| `nhanvien1` | Lê Văn Cường | Nhân viên kinh doanh | Cá nhân (Miền Bắc) |
| `nhanvien2` | Phạm Thị Dung | Nhân viên kinh doanh | Cá nhân (Miền Bắc) |
| `truongnhom2` | Hoàng Văn Em | Trưởng nhóm | Nhóm kinh doanh Miền Nam |
| `nhanvien3` | Vũ Thị Giang | Nhân viên kinh doanh | Cá nhân (Miền Nam) |
| `quantri` | Quản trị viên | Quản trị hệ thống | Quản trị cấu hình |

---

## 5. Danh mục Module & Quy chuẩn Nghiệp vụ

### 5.1. Phân hệ Cơ hội bán hàng (SCRUM-87)
* **Endpoint chính:** `POST /api/opportunities`, `GET /api/opportunities`, `PATCH /api/opportunities/{id}`.
* **Nghiệp vụ:** Khai báo thông tin thương vụ, người liên hệ thuộc khách hàng, giá trị dự kiến, nguồn và ngày dự kiến chốt. Xác suất thắng mặc định theo từng giai đoạn; khi người dùng tự điều chỉnh xác suất, hệ thống yêu cầu bắt buộc nhập lý do vào `probability_note`. Ngày chốt không được đặt ở quá khứ khi tạo mới.

### 5.2. Bảng Pipeline dạng Kanban (SCRUM-88)
* **Endpoint chính:** `GET /api/pipeline/board`, `POST /api/pipeline/cards/{id}/move`.
* **Nghiệp vụ:** Trực quan hoá đường ống bán hàng theo cột giai đoạn. Tính toán số lượng thương vụ, tổng doanh số và doanh số kỳ vọng theo xác suất. Thẻ cơ hội tự động phân tích và gắn cờ cảnh báo nếu thương vụ bị đình trệ quá ngưỡng quy định hoặc quá ngày chốt dự kiến.

### 5.3. Quản lý Sản phẩm / Dịch vụ & Hợp đồng thuê bao (SCRUM-89)
* **Endpoint chính:** `GET /api/products`, `POST /api/opportunities/{id}/lines`.
* **Nghiệp vụ:** Thêm sản phẩm từ danh mục niêm yết vào cơ hội. Tự động tính toán lại tổng giá trị hợp đồng khi có thay đổi dòng sản phẩm. Đối với dịch vụ thuê bao theo kỳ, hệ thống tự động bóc tách doanh số quy đổi năm (`annual_value`) và bảng phân bổ chu kỳ thanh toán.

### 5.4. Kiểm soát Ràng buộc Chuyển Giai đoạn - Stage Gates (SCRUM-90)
* **Endpoint chính:** `POST /api/stage-rules`, `GET /api/opportunities/{id}/stage-check`, `GET /api/stage-rules/overrides`.
* **Nghiệp vụ:** Giám đốc kinh doanh thiết lập điều kiện tiên quyết khi rời giai đoạn (ví dụ: bắt buộc phải có ít nhất 1 cuộc gặp đã diễn ra). Hệ thống chặn thao tác chuyển giai đoạn nếu thiếu điều kiện và trả về danh sách chi tiết các tiêu chí chưa đạt. Cho phép Trưởng nhóm trở lên thực hiện ghi đè (override) kèm lý do giải trình nhằm đảm bảo tính linh hoạt trong kinh doanh.

### 5.5. Nhật ký Tương tác Khách hàng (SCRUM-99)
* **Endpoint chính:** `POST /api/activities`, `POST /api/activities/quick`, `GET /api/customers/{id}/activities`.
* **Nghiệp vụ:** Ghi nhận 4 loại hình tương tác: Cuộc gọi, Cuộc gặp, Email và Ghi chú. Cho phép ghi bù các hoạt động đã diễn ra trong quá khứ hoặc lên lịch sắp tới. Cung cấp API ghi nhanh tối ưu cho thiết bị di động ngay sau khi hoàn thành buổi làm việc với khách hàng.

### 5.6. Quản lý Công việc & Hạn định (SCRUM-100)
* **Endpoint chính:** `POST /api/tasks`, `POST /api/tasks/{id}/complete`, `POST /api/tasks/{id}/postpone`.
* **Nghiệp vụ:** Quản lý danh sách đầu việc có hạn hoàn thành, gắn mức độ ưu tiên và liên kết với khách hàng/cơ hội. Hỗ trợ quy trình hoãn việc (bắt buộc nêu lý do) và lưu vết lịch sử hoãn. Trưởng nhóm có thẩm quyền giao việc cho các thành viên trong nhóm phụ trách.

---

## 6. Kiểm thử tự động (Automated Testing)

Dự án áp dụng phương pháp kiểm thử tự động với framework `unittest`, kiểm tra toàn diện 100% các tiêu chí chấp nhận (Acceptance Criteria):

```powershell
.\chay_kiem_thu.ps1
# hoặc: python -m unittest discover -s tests -t . -v
```

**Kết quả kiểm thử:**
* 73/73 tests đạt trạng thái **OK (Passed)**.
* Bao phủ các kịch bản phân quyền (RBAC), kiểm tra ràng buộc dữ liệu, tính toán tài chính và các trường hợp biên (edge cases).

---

## 7. Cấu trúc Thư mục Dự án

```
crm_backend/
├── app/
│   ├── __init__.py          # Khởi tạo Flask Application & đăng ký Blueprint
│   ├── auth.py              # Xử lý xác thực Token & giải mã phiên làm việc
│   ├── permissions.py       # Phân quyền truy cập theo vai trò (RBAC)
│   ├── schema.sql           # Cấu trúc CSDL SQLite3
│   ├── seed.py              # Dữ liệu mẫu ban đầu
│   ├── common/              # Module dùng chung (Auth, Lookups, Stages, Helpers)
│   └── features/            # Phân hệ nghiệp vụ theo domain
│       ├── opportunities/       # SCRUM-87: Quản lý cơ hội bán hàng
│       ├── pipeline/            # SCRUM-88: Bảng Kanban Pipeline
│       ├── opportunity_lines/   # SCRUM-89: Dòng sản phẩm & Dịch vụ
│       ├── stage_gates/         # SCRUM-90: Điều kiện ràng buộc giai đoạn
│       ├── activities/          # SCRUM-99: Nhật ký hoạt động tương tác
│       └── tasks/               # SCRUM-100: Quản lý công việc & hạn định
├── tests/                   # Bộ kiểm thử tự động theo từng phân hệ
├── run.py                   # Điểm khởi chạy ứng dụng chính
├── requirements.txt         # Khai báo các gói phụ thuộc
├── chay_server.ps1          # Script khởi chạy nhanh máy chủ
└── chay_kiem_thu.ps1        # Script chạy bộ kiểm thử tự động
```
