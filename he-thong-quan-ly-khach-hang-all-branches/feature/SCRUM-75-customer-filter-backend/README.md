# SCRUM-75: Bộ lọc nâng cao & Quản lý Bộ lọc đã lưu cho Khách hàng (Backend Python)

## 📌 Tổng quan Feature

User Story này cung cấp tính năng cho **Nhân viên kinh doanh & Chăm sóc khách hàng** thực hiện tìm kiếm và lọc nâng cao trên toàn bộ danh sách Khách hàng theo nhiều tiêu chí kết hợp, đồng thời cho phép lưu lại bộ lọc thường dùng để tái sử dụng nhanh chóng.

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Tìm kiếm đa trường** | API hỗ trợ tham số `q` tìm đồng thời trong: Tên khách hàng, Số điện thoại, Email, Địa chỉ và cả Mã số thuế (trường tùy chỉnh `tax_code`). |
| **2. Lọc theo Trạng thái** | Tham số `status` lọc theo trạng thái khách hàng (Tiềm năng, Đang hợp tác, Không hợp tác, v.v.). |
| **3. Lọc theo Ngành nghề / Quy mô / Khu vực** | Tham số `industry`, `scale`, `region` lọc qua các trường tùy chỉnh (custom fields) linh hoạt. |
| **4. Lọc theo Người sở hữu (Owner)** | Tham số `owner_id` lọc khách hàng theo nhân viên phụ trách. |
| **5. Phân trang & Sắp xếp** | Tham số `page`, `per_page`, `sort_by`, `order` kiểm soát phân trang và thứ tự kết quả. |
| **6. Quản lý Bộ lọc đã lưu (Saved Filters CRUD)** | API đầy đủ cho Tạo / Đọc / Cập nhật / Xóa bộ lọc đã lưu theo từng người dùng, lưu vào bảng `dbo.saved_filters`. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-75-customer-filter-backend/
├── README.md                               ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── scrum_75_customer_filter.sql        ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── customer_filters.py             ← ★ Module mới: Bộ lọc đa tiêu chí & Saved Filters
    │   ├── custom_fields.py                ← Tích hợp lọc theo custom fields
    │   ├── customers.py                    ← Quản lý Khách hàng
    │   ├── routes.py                       ← API Endpoints (thêm routes SCRUM-75)
    │   └── ...
    └── tests/
        ├── conftest.py
        └── test_customer_filter.py         ← ★ Test suite mới cho SCRUM-75
```

---

## 🗄️ Database Schema — Bảng mới

### `dbo.saved_filters`
Lưu trữ bộ lọc đã được người dùng đặt tên và lưu lại:
- `id` (INT, PK, IDENTITY)
- `user_id` (INT, FK → `dbo.users.id`) — Người tạo bộ lọc
- `name` (NVARCHAR(255)) — Tên bộ lọc do người dùng đặt
- `filter_target` (VARCHAR(50), default `'customer'`) — Loại đối tượng lọc
- `criteria_json` (NVARCHAR(MAX)) — JSON chứa các tiêu chí lọc đã lưu
- `created_at` / `updated_at` (BIGINT, Unix timestamp ms)

---

## 📡 Chi tiết API Endpoints

### 1. Tìm kiếm & Lọc Khách hàng
- `GET /api/customers/search-filter` — Tìm kiếm và lọc đa tiêu chí
  - Query params: `q`, `status`, `industry`, `scale`, `region`, `owner_id`, `page`, `per_page`, `sort_by`, `order`, `cf_<key>=value`
  - Response: `{ items: [...], total, page, per_page, total_pages }`

### 2. Quản lý Bộ lọc đã lưu (Saved Filters)
- `GET /api/saved-filters?target=customer` — Danh sách bộ lọc của người dùng hiện tại
- `POST /api/saved-filters` — Lưu bộ lọc mới
  - Body: `{ "name": "Tên bộ lọc", "criteria": {...}, "filter_target": "customer" }`
- `GET /api/saved-filters/<id>` — Chi tiết 1 bộ lọc đã lưu
- `PUT /api/saved-filters/<id>` — Cập nhật bộ lọc đã lưu
- `DELETE /api/saved-filters/<id>` — Xóa bộ lọc đã lưu

---

## 🧪 Kiểm thử Tự động (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_customer_filter.py -v
```

Kết quả kiểm thử: **Tất cả tests passed (100%)**.
