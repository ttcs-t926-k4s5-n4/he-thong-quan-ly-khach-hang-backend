# SCRUM-77: Chăm sóc Khách hàng Định kỳ & Lịch sử Tương tác (Backend Python)

## 📌 Tổng quan Feature

User Story này cung cấp tính năng **Danh sách Chăm sóc Định kỳ** — tự động liệt kê các khách hàng chưa được liên hệ trong N ngày gần nhất, ưu tiên theo giá trị hợp đồng. Nhân viên có thể **Ghi nhận tương tác** trực tiếp và hệ thống tự động cập nhật thời điểm liên hệ gần nhất để theo dõi liên tục.

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Danh sách Chăm sóc Định kỳ** | API `GET /api/customers/periodic-care?days=30` trả về khách hàng chưa có tương tác trong N ngày, sắp xếp ưu tiên theo tổng giá trị cơ hội (`total_contract_value DESC`). |
| **2. Ghi nhận Tương tác** | API `POST /api/customers/<id>/interactions` lưu bản ghi tương tác vào `dbo.customer_interactions` và tự động cập nhật `last_interaction_at` trên bảng `dbo.customers`. |
| **3. Đánh dấu Đã liên hệ Nhanh** | API `POST /api/customers/<id>/mark-contacted` cho phép đánh dấu đã liên hệ ngay từ danh sách chăm sóc định kỳ với 1 thao tác. |
| **4. Xem Lịch sử Tương tác** | API `GET /api/customers/<id>/interactions` trả về toàn bộ lịch sử tương tác của 1 khách hàng, sắp xếp mới nhất lên trên. |
| **5. Phân trang & Thông tin bổ sung** | Response tự động tính toán `days_without_interaction` (số ngày chưa tương tác), `contract_value` và gắn thêm Custom Fields cho từng khách hàng. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-77-periodic-care-backend/
├── README.md                               ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── scrum_77_periodic_care.sql          ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── periodic_care.py                ← ★ Module mới: Danh sách định kỳ & Tương tác
    │   ├── customers.py                    ← Tích hợp cột last_interaction_at
    │   ├── routes.py                       ← API Endpoints (thêm routes SCRUM-77)
    │   └── ...
    └── tests/
        ├── conftest.py
        └── test_periodic_customer_care.py  ← ★ Test suite mới cho SCRUM-77
```

---

## 🗄️ Database Schema — Thay đổi DB

### Bảng mới: `dbo.customer_interactions`
Lưu toàn bộ lịch sử tương tác chăm sóc khách hàng:
- `id` (INT, PK, IDENTITY)
- `customer_id` (INT, FK → `dbo.customers.id`)
- `interaction_type` (NVARCHAR(50), default `'Gọi điện chăm sóc'`)
  - Ví dụ: `'Gọi điện chăm sóc'` | `'Gửi email'` | `'Gặp trực tiếp'` | `'Đánh dấu đã liên hệ ngay'`
- `notes` (NVARCHAR(MAX)) — Ghi chú nội dung tương tác
- `created_by` (INT, FK → `dbo.users.id`)
- `created_at` (BIGINT, Unix ms)

### Cột mới trong `dbo.customers`:
- `last_interaction_at` (BIGINT) — Unix timestamp (ms) của lần tương tác gần nhất. Tự động cập nhật mỗi khi ghi nhận tương tác mới.

---

## 📡 Chi tiết API Endpoints

### 1. Danh sách Chăm sóc Định kỳ
- `GET /api/customers/periodic-care` — Danh sách khách hàng cần chăm sóc
  - Query params: `days` (default=30), `page`, `per_page`
  - Response: `{ items: [...days_without_interaction, contract_value, custom_fields...], total, days_threshold, page, per_page, total_pages }`

### 2. Lịch sử & Ghi nhận Tương tác
- `GET /api/customers/<id>/interactions` — Lịch sử tương tác của 1 khách hàng (mới nhất → cũ nhất)
- `POST /api/customers/<id>/interactions` — Ghi nhận tương tác mới
  - Body: `{ "interaction_type": "Gọi điện chăm sóc", "notes": "..." }`
- `POST /api/customers/<id>/mark-contacted` — Đánh dấu đã liên hệ nhanh (1 click)
  - Body: `{ "notes": "..." }` (tùy chọn)

---

## 🧪 Kiểm thử Tự động (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_periodic_customer_care.py -v
```

Kết quả kiểm thử: **Tất cả tests passed (100%)**.
