# SCRUM-76: Yêu cầu Hỗ trợ Sau bán & Gắn cờ Rủi ro Rời bỏ (Backend Python)

## 📌 Tổng quan Feature

User Story này cung cấp hệ thống **Quản lý Yêu cầu Hỗ trợ Sau bán (Support Tickets)** cho bộ phận Chăm sóc khách hàng, kết hợp với engine **Tự động Gắn cờ Rủi ro Rời bỏ (Churn Risk Flagging)** — giúp Nhân viên kinh doanh phụ trách nhận cảnh báo kịp thời khi khách hàng có nguy cơ mất đi.

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Tạo & Quản lý Yêu cầu Hỗ trợ** | CRUD đầy đủ cho `dbo.support_tickets`. Mỗi ticket có: Tiêu đề, Mô tả, Mức độ ưu tiên (`low`/`medium`/`high`/`urgent`), Trạng thái (`open`/`in_progress`/`resolved`/`closed`), Người xử lý (`assignee_id`). |
| **2. Tự động sinh Mã ticket** | Mỗi ticket tạo mới được cấp mã duy nhất theo định dạng `TK-XXXXXX` (timestamp-based). |
| **3. Engine Gắn cờ Rủi ro Rời bỏ (Auto Churn Risk)** | Sau mỗi thao tác Tạo / Cập nhật / Xóa ticket, hệ thống tự động gọi `evaluate_and_update_churn_risk()`. Logic: ≥ 2 ticket tồn đọng → Gắn cờ rủi ro. Có ticket `urgent` chưa xử lý → Gắn cờ rủi ro khẩn cấp. |
| **4. Góc nhìn 360° Khách hàng** | API `GET /api/customers/<id>/360` trả về toàn bộ: Thông tin khách hàng + Custom Fields + Danh sách Support Tickets + Danh sách Cơ hội liên quan + Cảnh báo Churn Risk (nếu có). |
| **5. Danh sách Cảnh báo Rủi ro** | API `GET /api/churn-risk-alerts` trả về danh sách tất cả khách hàng đang bị gắn cờ rủi ro rời bỏ để NVKD phụ trách xử lý ngay. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-76-support-tickets-backend/
├── README.md                                   ← Tài liệu hướng dẫn & API Spec
├── database/
│   └── scrum_76_support_tickets.sql            ← SQL Schema cho SQL Server 2019+
└── backend/
    ├── app/
    │   ├── support_tickets.py                  ← ★ Module mới: Support Tickets & Churn Risk Engine
    │   ├── customers.py                        ← Tích hợp cột is_churn_risk, churn_risk_reason
    │   ├── routes.py                           ← API Endpoints (thêm routes SCRUM-76)
    │   └── ...
    └── tests/
        ├── conftest.py
        └── test_support_tickets_churn_risk.py  ← ★ Test suite mới cho SCRUM-76
```

---

## 🗄️ Database Schema — Thay đổi DB

### Bảng mới: `dbo.support_tickets`
Lưu trữ tất cả yêu cầu hỗ trợ sau bán:
- `id` (INT, PK, IDENTITY)
- `ticket_code` (VARCHAR(50), UNIQUE) — Mã ticket tự động `TK-XXXXXX`
- `customer_id` (INT, FK → `dbo.customers.id`)
- `title` (NVARCHAR(255)) — Tiêu đề yêu cầu hỗ trợ
- `description` (NVARCHAR(MAX)) — Mô tả chi tiết
- `priority` (VARCHAR(20)) — `low` | `medium` | `high` | `urgent`
- `status` (VARCHAR(20)) — `open` | `in_progress` | `resolved` | `closed`
- `assignee_id` (INT, FK → `dbo.users.id`) — Người xử lý
- `created_by` (INT, FK → `dbo.users.id`)
- `created_at` / `updated_at` (BIGINT, Unix ms)

### Cột mới trong `dbo.customers`:
- `is_churn_risk` (BIT, default 0) — Cờ rủi ro rời bỏ (tự động cập nhật)
- `churn_risk_reason` (NVARCHAR(500)) — Lý do được gắn cờ rủi ro
- `last_interaction_at` (BIGINT) — Thời điểm tương tác gần nhất

---

## 📡 Chi tiết API Endpoints

### 1. Quản lý Yêu cầu Hỗ trợ (Support Tickets)
- `GET /api/support-tickets` — Danh sách & Lọc ticket
  - Query params: `customer_id`, `status`, `priority`, `assignee_id`, `page`, `per_page`
- `POST /api/support-tickets` — Tạo ticket mới
  - Body: `{ customer_id, title, description, priority, status, assignee_id }`
- `GET /api/support-tickets/<id>` — Chi tiết 1 ticket
- `PUT /api/support-tickets/<id>` — Cập nhật ticket (đổi trạng thái, người xử lý, ...)
- `DELETE /api/support-tickets/<id>` — Xóa ticket

### 2. Cảnh báo & Góc nhìn 360°
- `GET /api/customers/<id>/360` — Góc nhìn 360° Khách hàng (info + tickets + opportunities + churn alert)
- `GET /api/churn-risk-alerts` — Danh sách khách hàng đang bị cảnh báo rủi ro rời bỏ

---

## 🧪 Kiểm thử Tự động (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_support_tickets_churn_risk.py -v
```

Kết quả kiểm thử: **Tất cả tests passed (100%)**.
