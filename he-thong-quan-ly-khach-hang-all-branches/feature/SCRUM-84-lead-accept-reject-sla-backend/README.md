# SCRUM-84: Nhận/Từ chối Lead với ràng buộc SLA phản hồi (Backend Python)

## 📌 Tổng quan Feature

User Story: **"Là Nhân viên kinh doanh, tôi muốn nhận hoặc từ chối lead được phân, có ràng buộc SLA phản hồi, để lead không nằm im ba ngày rồi nguội hẳn."**

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Nhận lead → chuyển sang Đang chăm sóc** | API `POST /api/leads/<id>/accept` — chỉ nhân viên được phân công; cập nhật `status = 'Đang chăm sóc'` + ghi activity. |
| **2. Từ chối bắt buộc nhập lý do** | API `POST /api/leads/<id>/reject` — validate `reason` bắt buộc; trả 400 nếu thiếu; lead quay về `status = 'Chờ phân bổ'`, tăng `rejection_count`. |
| **3. Quá SLA → gắn cờ & báo trưởng nhóm** | `check_and_flag_sla_breached_leads()` quét lead `status='Đã phân công'` quá `sla_deadline_at`, gắn `sla_breached=1`, ghi activity cảnh báo. API `GET /api/leads/sla-breached` + `POST /api/leads/check-sla` dành cho manager. |
| **4. SLA tính từ thời điểm phân công** | `assign_lead()` ghi `assigned_at = now` và `sla_deadline_at = assigned_at + 3 ngày (ms)`. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-84-lead-accept-reject-sla-backend/
├── README.md
├── database/
│   └── scrum_84_lead_accept_reject_sla.sql     ← Bảng leads + lead_activities
└── backend/
    ├── app/
    │   ├── leads.py                             ← ★ Module mới: Vòng đời Lead + SLA
    │   └── routes.py                            ← API Endpoints (thêm routes SCRUM-84)
    └── tests/
        └── test_lead_accept_reject_sla.py       ← ★ Test suite cho SCRUM-84
```

---

## 🗄️ Database Schema — Thay đổi DB

### Bảng mới: `dbo.leads`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `full_name` | NVARCHAR(255) | Tên lead (bắt buộc) |
| `email`, `phone`, `company` | NVARCHAR | Thông tin liên hệ |
| `source` | NVARCHAR(100) | Nguồn: Facebook, Zalo, Website... |
| `classification` | VARCHAR(10) | `hot` / `warm` / `cold` |
| `status` | NVARCHAR(50) | `Mới` / `Đã phân công` / `Đang chăm sóc` / `Chờ phân bổ` / `Đã chuyển đổi` |
| `assigned_to` | INT FK | Nhân viên được phân công |
| `assigned_at` | BIGINT | Unix ms khi phân công |
| `sla_deadline_at` | BIGINT | `assigned_at + 3 ngày` |
| `sla_breached` | BIT | 1 = đã vi phạm SLA |
| `sla_alert_sent` | BIT | 1 = đã gửi cảnh báo |
| `rejection_reason` | NVARCHAR(1000) | Lý do từ chối (bắt buộc khi reject) |
| `rejection_count` | INT | Số lần bị từ chối |

### Bảng mới: `dbo.lead_activities`
Ghi lịch sử mọi hành động trên lead: `created` / `assigned` / `accepted` / `rejected` / `sla_breached` / `converted` / `updated`.

---

## 📡 Chi tiết API Endpoints (SCRUM-84)

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/api/leads` | All | Danh sách lead (nhân viên chỉ thấy của mình) |
| `POST` | `/api/leads` | All | Tạo lead mới |
| `GET` | `/api/leads/<id>` | All | Chi tiết lead |
| `PUT` | `/api/leads/<id>` | All | Cập nhật thông tin lead |
| `DELETE` | `/api/leads/<id>` | admin/manager | Xóa lead |
| `POST` | `/api/leads/<id>/assign` | admin/manager | Phân công lead cho nhân viên |
| `POST` | `/api/leads/<id>/accept` | employee | **Nhận lead** → Đang chăm sóc |
| `POST` | `/api/leads/<id>/reject` | employee | **Từ chối lead** (bắt buộc nhập lý do) |
| `GET` | `/api/leads/sla-breached` | admin/manager | Danh sách lead vi phạm SLA |
| `POST` | `/api/leads/check-sla` | admin/manager | Quét & gắn cờ SLA vi phạm |
| `GET` | `/api/leads/<id>/activities` | All | Lịch sử hoạt động của lead |

### Ví dụ: Từ chối lead
```http
POST /api/leads/42/reject
Content-Type: application/json
{ "reason": "Khách hàng không đúng phân khúc mục tiêu" }
```
Response `200`:
```json
{
  "message": "Đã từ chối lead. Lead quay về hàng chờ phân bổ.",
  "lead": { "id": 42, "status": "Chờ phân bổ", "rejection_count": 1, ... }
}
```
Thiếu `reason` → Response `400`:
```json
{
  "message": "Vui lòng nhập lý do từ chối.",
  "errors": { "reason": "Lý do từ chối là bắt buộc." }
}
```

### Ví dụ: SLA Status trong response
```json
{
  "sla_status": "breached",   // "ok" | "warning" | "breached" | "not_assigned"
  "sla_deadline_at": 1728547200000
}
```

---

## 🧪 Kiểm thử Tự động

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_accept_reject_sla.py -v
```
