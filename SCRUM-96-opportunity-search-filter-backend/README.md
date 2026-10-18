# SCRUM-96: Tìm kiếm, Lọc & Lưu bộ lọc Cơ hội kinh doanh (Opportunity Search & Filter) — Backend Python

## 📌 1. Tổng quan Feature

User Story: **"Là Nhân viên kinh doanh, tôi muốn tìm kiếm cơ hội theo nhiều điều kiện và lưu các bộ lọc thường dùng để nhanh chóng tìm lại những thương vụ cần thúc đẩy chốt sale."**

Feature này cung cấp công cụ tìm kiếm và lọc cơ hội đa tiêu chí mạnh mẽ, phân trang và sắp xếp an toàn, đồng thời cho phép người dùng lưu lại các bộ lọc tùy chỉnh cá nhân (Saved Filters) để tái sử dụng với một thao tác.

---

## 🔥 2. Các Yêu cầu & Đáp ứng Backend

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Tìm kiếm đa trường** | `keyword` tìm đồng thời theo tên cơ hội, mã cơ hội (ID) và tên khách hàng liên quan. |
| **2. Lọc đa điều kiện** | Hỗ trợ kết hợp: `stage`, `min_value`, `max_value`, `close_date_from`, `close_date_to`, `product_id`, `owner_id`, và các trường tùy chỉnh (`cf_*`). |
| **3. Validation chặt chẽ** | Kiểm tra `min_value <= max_value` và `close_date_from <= close_date_to` (trả về HTTP 400 nếu vi phạm). |
| **4. Sắp xếp an toàn (Whitelist)** | Chỉ cho phép sắp xếp theo các trường: `created_at`, `value`, `stage`, `expected_close_date`, `title`, `id`. Ngăn chặn SQL Injection qua `ORDER BY`. |
| **5. Phân quyền dữ liệu (RBAC Data Scope)** | Nhân viên kinh doanh (`employee`) tự động được lọc chỉ thấy cơ hội do mình sở hữu hoặc được chia sẻ (SCRUM-97); Quản lý (`manager`) và Admin thấy toàn bộ. |
| **6. Quản lý Bộ lọc đã lưu (Saved Filters)** | Cung cấp đầy đủ RESTful API (Tạo, Xem danh sách, Chi tiết, Sửa, Xóa). Kiểm tra quyền sở hữu bộ lọc (HTTP 403 nếu truy cập của người khác). |
| **7. Bảo mật cấu hình** | Tự động lọc bỏ các thông tin nhạy cảm (token, password, secret) trước khi lưu vào `filter_config`. |

---

## 📂 3. Cấu trúc thư mục Feature

```
SCRUM-96-opportunity-search-filter-backend/
├── README.md                                    ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_96_opportunity_filters.sql        ← Migration CSDL: bảng saved_opportunity_filters + cột product_id
└── backend/
    ├── app/
    │   ├── opportunity_filters.py               ← ★ Module mới: Tìm kiếm, lọc nâng cao & CRUD Saved Filters
    │   ├── opportunities.py                     ← Module Cơ hội
    │   ├── routes.py                            ← API Endpoints (GET /opportunities + /opportunity-filters)
    │   └── ...                                  ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_opportunity_filters.py         ← ★ Bộ kiểm thử tự động toàn diện (13 test cases)
```

---

## 🗄️ 4. Database Schema & Migration

### Bảng mới: `dbo.saved_opportunity_filters`
Lưu trữ các cấu hình bộ lọc được cá nhân hóa cho từng người dùng:

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `INT` | `IDENTITY(1,1) PRIMARY KEY` | Khóa chính tự tăng |
| `user_id` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id) ON DELETE CASCADE` | ID người dùng sở hữu bộ lọc |
| `filter_name` | `NVARCHAR(255)` | `NOT NULL` | Tên bộ lọc do người dùng đặt |
| `filter_config` | `NVARCHAR(MAX)` | `NOT NULL` | Chuỗi JSON chứa các tiêu chí lọc đã lưu |
| `created_at` | `BIGINT` | `NOT NULL` | Thời điểm tạo (UTC epoch ms) |
| `updated_at` | `BIGINT` | `NOT NULL` | Thời điểm cập nhật (UTC epoch ms) |

### Index tối ưu:
- `IX_saved_opp_filters_user_id` trên `(user_id, created_at DESC)`: Tối ưu tải danh sách bộ lọc của người dùng hiện tại.

### Cột bổ sung trong `dbo.opportunities`:
- `product_id INT NULL`: Lưu trữ ID sản phẩm liên quan đến cơ hội.

---

## 📡 5. Chi tiết API Endpoints

### 1. `GET /api/opportunities` (Tìm kiếm & Lọc cơ hội)
- **Query Parameters**:
  - `keyword`: Tìm theo tên, mã cơ hội, tên khách hàng
  - `stage`: Giai đoạn bán hàng
  - `min_value`, `max_value`: Khoảng giá trị
  - `close_date_from`, `close_date_to`: Khoảng ngày chốt dự kiến
  - `product_id`: Lọc theo ID sản phẩm
  - `owner_id`: Lọc theo ID người sở hữu
  - `sort_by`: `created_at`, `value`, `stage`, `expected_close_date`, `title`, `id`
  - `sort_order`: `asc` hoặc `desc` (mặc định: `desc`)
  - `page`: Số trang (mặc định: `1`)
  - `page_size`: Số bản ghi mỗi trang (mặc định: `20`, hỗ trợ alias `per_page`)
- **Response**: Trả về `items`, `total`, `page`, `page_size`, `total_pages`, `sort_by`, `sort_order`.

### 2. Quản lý Bộ lọc đã lưu (`/api/opportunity-filters`)
- `POST /api/opportunity-filters`: Tạo bộ lọc mới
- `GET /api/opportunity-filters`: Lấy danh sách bộ lọc của người dùng hiện tại
- `GET /api/opportunity-filters/<id>`: Lấy chi tiết bộ lọc
- `PUT /api/opportunity-filters/<id>`: Cập nhật bộ lọc
- `DELETE /api/opportunity-filters/<id>`: Xóa bộ lọc

---

## 🧪 6. Hướng dẫn Chạy Kiểm thử (Testing)

```bash
cd backend
python -m unittest tests/test_opportunity_filters.py -v
```

Kết quả: **13/13 tests passed (100% OK)**.
