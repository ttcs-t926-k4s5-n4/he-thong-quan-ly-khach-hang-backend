# SCRUM-17 / SCRUM-66: Khai báo trường tùy chỉnh cho Khách hàng & Cơ hội (Backend Python)

## 📌 Tổng quan Feature

User Story này cung cấp tính năng cho phép **Quản trị hệ thống (System Admin)** định nghĩa các **trường tùy chỉnh (Custom Fields)** động cho 2 đối tượng kinh doanh chính:
1. **Khách hàng (`customer`)**
2. **Cơ hội kinh doanh (`opportunity`)**

Nhờ đó, nhân viên có thể đưa các thông tin/cột dữ liệu đang theo dõi ngoài Excel vào hệ thống một cách linh hoạt, đồng bộ và có kiểm soát dữ liệu.

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Khai báo kiểu dữ liệu** | Hỗ trợ 4 kiểu: `text` (văn bản), `number` (số), `date` (ngày YYYY-MM-DD), `select` (danh sách chọn kèm các tùy chọn options dạng JSON). |
| **2. Bắt buộc hay không (`is_required`)** | Cấu hình cờ `is_required` (True/False). Khi lưu thông tin Khách hàng/Cơ hội, hệ thống tự động kiểm tra và trả về phản hồi lỗi chi tiết nếu thiếu dữ liệu bắt buộc. |
| **3. Hiển thị trong Biểu mẫu (Form Schema)** | API `/api/custom-fields/schema/<entity_type>` cung cấp cấu hình trường động cho Frontend tự động render form nhập liệu kèm validate. |
| **4. Hiển thị trong Bộ lọc (Filter Engine)** | Các API danh sách `/api/customers` và `/api/opportunities` hỗ trợ lọc động theo trường tùy chỉnh qua query parameters `cf_<field_key>=value`. |
| **5. Xuất bản Excel (Excel Export Engine)** | Các API `/api/customers/export-excel` và `/api/opportunities/export-excel` tạo file Excel (`.xlsx`) chuyên nghiệp với tiêu đề động chứa tất cả các trường tùy chỉnh đang kích hoạt. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-66-custom-fields-backend/
├── README.md                           ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── scrum_66_custom_fields.sql      ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── __init__.py                 ← Application factory & CORS configuration
    │   ├── auth.py                     ← Authentication & Session Management
    │   ├── custom_fields.py            ← Module định nghĩa, validate & lưu trữ trường tùy chỉnh
    │   ├── customers.py                ← Quản lý Khách hàng tích hợp trường tùy chỉnh
    │   ├── db.py                       ← Kết nối PyODBC với SQL Server
    │   ├── excel_export.py             ← Exporter tạo file Excel (.xlsx) động
    │   ├── opportunities.py            ← Quản lý Cơ hội kinh doanh tích hợp trường tùy chỉnh
    │   └── routes.py                   ← API Endpoints
    ├── tests/
    │   ├── conftest.py
    │   └── test_custom_fields.py       ← Automated integration test suite
    ├── requirements.txt                ← Python dependencies (Flask, pyodbc, openpyxl, pytest)
    ├── run.py                          ← Script khởi chạy Flask backend
    └── seed_data.py                    ← Seed dữ liệu mẫu (User, Custom Fields, Customers, Opportunities)
```

---

## 🗄️ Database Schema

### 1. `dbo.custom_field_definitions`
Lưu định nghĩa các trường tùy chỉnh do Admin tạo:
- `id` (INT, PK)
- `entity_type` (NVARCHAR(50), 'customer' | 'opportunity')
- `field_key` (NVARCHAR(100), Unique key per entity)
- `field_label` (NVARCHAR(200), Nhãn hiển thị)
- `field_type` (NVARCHAR(50), 'text' | 'number' | 'date' | 'select')
- `options` (NVARCHAR(MAX), JSON array cho kiểu 'select')
- `is_required` (BIT, Bắt buộc hay không)
- `description` (NVARCHAR(500))
- `display_order` (INT)
- `is_active` (BIT)

### 2. `dbo.custom_field_values`
Lưu giá trị của trường tùy chỉnh cho từng bản ghi:
- `id` (BIGINT, PK)
- `entity_type` (NVARCHAR(50))
- `entity_id` (INT, Customer ID hoặc Opportunity ID)
- `field_id` (INT, FK tới `custom_field_definitions.id`)
- `field_value` (NVARCHAR(MAX))

---

## 📡 Chi tiết API Endpoints

### 1. Định nghĩa Trường Tùy chỉnh (Admin Only)
- `GET /api/custom-fields?entity_type=customer|opportunity` — Danh sách các trường tùy chỉnh
- `GET /api/custom-fields/schema/<entity_type>` — Form schema render tự động cho Frontend
- `POST /api/custom-fields` — Tạo trường tùy chỉnh mới (Admin)
- `GET /api/custom-fields/<id>` — Chi tiết 1 trường
- `PUT /api/custom-fields/<id>` — Cập nhật trường tùy chỉnh (Admin)
- `DELETE /api/custom-fields/<id>` — Xóa trường tùy chỉnh (Admin)

### 2. Quản lý Khách hàng & Cơ hội kinh doanh
- `GET /api/customers?q=search&status=Mới&cf_industry=Công+nghệ` — Danh sách & Lọc theo trường tùy chỉnh
- `POST /api/customers` — Tạo khách hàng mới kèm object `custom_fields: {"industry": "Công nghệ"}`
- `PUT /api/customers/<id>` — Cập nhật khách hàng & trường tùy chỉnh
- `DELETE /api/customers/<id>` — Xóa khách hàng
- `GET /api/customers/export-excel` — Tải file Excel (`.xlsx`) danh sách Khách hàng có đầy đủ cột tùy chỉnh
- `GET /api/opportunities?q=search&stage=Đàm+phán&cf_lead_source=Website` — Danh sách & Lọc Cơ hội
- `POST /api/opportunities` — Tạo cơ hội kinh doanh kèm trường tùy chỉnh
- `PUT /api/opportunities/<id>` — Cập nhật cơ hội
- `DELETE /api/opportunities/<id>` — Xóa cơ hội
- `GET /api/opportunities/export-excel` — Tải file Excel (`.xlsx`) danh sách Cơ hội có đầy đủ cột tùy chỉnh

---

## 🧪 Kiểm thử Tự động (Automated Testing)

Chạy bộ test tích hợp với command:
```powershell
cd backend
.venv\Scripts\pytest tests/test_custom_fields.py
```
Kết quả kiểm thử: **9/9 tests passed (100%)**.
