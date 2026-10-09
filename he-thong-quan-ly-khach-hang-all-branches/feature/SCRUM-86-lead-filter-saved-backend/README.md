# SCRUM-86: Danh sách Lead với Bộ lọc nâng cao + Bộ lọc lưu sẵn (Backend Python)

## 📌 Tổng quan Feature

User Story: **"Là Nhân viên kinh doanh, tôi muốn xem danh sách lead với bộ lọc và bộ lọc lưu sẵn, để mở máy buổi sáng là biết ngay hôm nay cần gọi ai."**

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Lọc theo trạng thái, nguồn, phân loại nóng/ấm/lạnh, người phụ trách, khoảng thời gian** | API `GET /api/leads/search-filter` nhận query params: `status`, `source`, `classification` (hot/warm/cold), `assigned_to`, `date_from`, `date_to`. Hỗ trợ tìm kiếm full-text `q` và phân trang. |
| **2. Lead quá SLA hiển thị nổi bật** | Mỗi lead trong response kèm `sla_status`: `"ok"` / `"warning"` / `"breached"`. Frontend dùng trường này để tô màu nổi bật. Có thể lọc `sla_breached_only=true` để chỉ xem lead vi phạm. |
| **3. Lưu và đặt tên cho bộ lọc hay dùng** | CRUD API `/api/lead-saved-filters`: tạo, đọc, sửa, xóa. Tiêu chí lưu dưới dạng JSON. API `GET /api/lead-saved-filters/<id>/apply` áp dụng ngay bộ lọc đã lưu. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-86-lead-filter-saved-backend/
├── README.md
├── database/
│   └── scrum_86_lead_filter_saved.sql           ← Bảng leads + lead_saved_filters
└── backend/
    ├── app/
    │   ├── leads.py                             ← Module Lead (từ SCRUM-84)
    │   ├── lead_filters.py                      ← ★ Module mới: Bộ lọc Lead + Saved Filters
    │   └── routes.py                            ← API Endpoints (thêm routes SCRUM-86)
    └── tests/
        └── test_lead_filter_saved.py            ← ★ Test suite cho SCRUM-86
```

---

## 🗄️ Database Schema — Thay đổi DB

### Bảng mới: `dbo.lead_saved_filters`
Lưu bộ lọc lead của từng nhân viên:

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `user_id` | INT FK | Chủ sở hữu bộ lọc |
| `name` | NVARCHAR(255) | Tên gợi nhớ: "Leads nóng tuần này", "Cần gọi hôm nay" |
| `criteria_json` | NVARCHAR(MAX) | JSON chứa các tiêu chí lọc |
| `created_at`, `updated_at` | BIGINT | Timestamp Unix ms |

---

## 📡 Chi tiết API Endpoints (SCRUM-86)

### Bộ lọc Lead nâng cao
| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/api/leads/search-filter` | All | **Lọc lead** theo nhiều điều kiện + SLA nổi bật |

**Query params hỗ trợ:**
| Param | Kiểu | Mô tả |
|---|---|---|
| `q` | string | Tìm kiếm theo tên, email, phone, công ty |
| `status` | string | `Mới` / `Đã phân công` / `Đang chăm sóc` / `Chờ phân bổ` |
| `source` | string | Nguồn lead (Facebook, Website, Zalo...) |
| `classification` | string | `hot` / `warm` / `cold` |
| `assigned_to` | int | ID nhân viên phụ trách |
| `date_from` | int | Unix ms - từ ngày tạo |
| `date_to` | int | Unix ms - đến ngày tạo |
| `sla_breached_only` | bool | `true` = chỉ hiện lead vi phạm SLA |
| `sort_by` | string | `created_at` / `sla_deadline_at` / `status` / `classification` |
| `order` | string | `asc` / `desc` |
| `page`, `per_page` | int | Phân trang |

### Bộ lọc đã lưu sẵn
| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/api/lead-saved-filters` | All | Danh sách bộ lọc đã lưu của user |
| `POST` | `/api/lead-saved-filters` | All | **Lưu bộ lọc** với tên gợi nhớ |
| `GET` | `/api/lead-saved-filters/<id>` | All | Chi tiết bộ lọc |
| `PUT` | `/api/lead-saved-filters/<id>` | All | Cập nhật tên/tiêu chí |
| `DELETE` | `/api/lead-saved-filters/<id>` | All | Xóa bộ lọc |
| `GET` | `/api/lead-saved-filters/<id>/apply` | All | **Áp dụng bộ lọc** → trả về danh sách lead |

### Ví dụ: Lưu bộ lọc "Leads nóng cần gọi hôm nay"
```http
POST /api/lead-saved-filters
{
  "name": "Leads nóng cần gọi hôm nay",
  "criteria": {
    "classification": "hot",
    "status": "Đang chăm sóc",
    "assigned_to": 5,
    "sort_by": "sla_deadline_at",
    "order": "asc"
  }
}
```
Response `201`:
```json
{
  "message": "Lưu bộ lọc lead thành công.",
  "saved_filter": {
    "id": 3,
    "name": "Leads nóng cần gọi hôm nay",
    "criteria": { "classification": "hot", "status": "Đang chăm sóc", ... }
  }
}
```

### Ví dụ: Áp dụng bộ lọc đã lưu
```http
GET /api/lead-saved-filters/3/apply?page=1&per_page=20
```
→ Trả về danh sách lead phù hợp với tiêu chí đã lưu, kèm `sla_status` cho từng lead.

### sla_status trong response
```json
{
  "sla_status": "breached",   // ← Frontend tô đỏ nổi bật
  "sla_deadline_at": 1728547200000
}
```
| Giá trị | Ý nghĩa | Frontend |
|---|---|---|
| `"ok"` | SLA còn > 8 giờ | Xanh/bình thường |
| `"warning"` | SLA còn < 8 giờ | Vàng cảnh báo |
| `"breached"` | Đã vượt SLA | Đỏ nổi bật |
| `"not_assigned"` | Chưa phân công | Xám |

---

## 🧪 Kiểm thử Tự động

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_filter_saved.py -v
```
