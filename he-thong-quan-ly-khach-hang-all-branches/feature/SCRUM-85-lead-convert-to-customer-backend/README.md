# SCRUM-85: Chuyển Lead thành Khách hàng, Người liên hệ và Cơ hội bán hàng (Backend Python)

## 📌 Tổng quan Feature

User Story: **"Là Nhân viên kinh doanh, tôi muốn chuyển một lead đủ điều kiện thành khách hàng và cơ hội, để không phải nhập lại thông tin đã hỏi khách ba lần."**

---

## 🔥 Các Yêu cầu & Đáp ứng (Requirement Specifications)

| Yêu cầu Story | Giải pháp & Đáp ứng Backend |
|---|---|
| **1. Một thao tác sinh đồng thời 3 đối tượng** | API `POST /api/leads/<id>/convert` tạo nguyên tử: `dbo.customers` + `dbo.lead_contacts` + `dbo.opportunities`. Nếu bất kỳ bước nào lỗi, toàn bộ rollback. |
| **2. Dữ liệu lead chuyển sang, không nhập lại** | `convert_lead_to_customer()` tự động dùng `lead.full_name`, `lead.email`, `lead.phone`, `lead.company` → không cần frontend truyền lại. |
| **3. Lead chuyển sang 'Đã chuyển đổi' và không sửa được** | `UPDATE dbo.leads SET status='Đã chuyển đổi'`. Mọi thao tác sửa/assign/accept/reject sau đó đều raise `ValueError("lead_already_converted")`. |
| **4. Toàn bộ hoạt động lead được giữ lại trên khách hàng mới** | `convert_lead_to_customer()` nhân bản toàn bộ `dbo.lead_activities` → `dbo.customer_interactions` với tiền tố `[Từ lead #id]`. |

---

## 📂 Cấu trúc thư mục Feature

```
SCRUM-85-lead-convert-to-customer-backend/
├── README.md
├── database/
│   └── scrum_85_lead_convert_to_customer.sql   ← Bảng leads + lead_contacts
└── backend/
    ├── app/
    │   ├── leads.py                             ← Module Lead (từ SCRUM-84)
    │   ├── lead_convert.py                      ← ★ Module mới: Chuyển đổi Lead
    │   └── routes.py                            ← API Endpoints (thêm routes SCRUM-85)
    └── tests/
        └── test_lead_convert_to_customer.py     ← ★ Test suite cho SCRUM-85
```

---

## 🗄️ Database Schema — Thay đổi DB

### Bảng mới: `dbo.lead_contacts`
Lưu thông tin người liên hệ (Contact Person) của khách hàng doanh nghiệp được tạo từ chuyển đổi lead:

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `customer_id` | INT FK | FK → `dbo.customers.id` |
| `lead_id` | INT FK | FK → `dbo.leads.id` (nguồn gốc) |
| `full_name` | NVARCHAR(255) | Tên người liên hệ (từ lead) |
| `email` | NVARCHAR(255) | Email (từ lead) |
| `phone` | NVARCHAR(50) | Số điện thoại (từ lead) |
| `position` | NVARCHAR(255) | Chức vụ (tùy chọn) |
| `is_primary` | BIT | Luôn = 1 khi tạo từ lead |

---

## 📡 Chi tiết API Endpoints (SCRUM-85)

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `POST` | `/api/leads/<id>/convert` | All | **Chuyển đổi lead** thành KH + Người LH + Cơ hội |
| `GET` | `/api/customers/<id>/contacts` | All | Danh sách người liên hệ của KH |
| *(Thừa kế)* | `/api/leads/*` | | Tất cả API SCRUM-84 |

### Request Body cho `/api/leads/<id>/convert`
```json
{
  "company_name": "Công ty TNHH ABC",        // Nếu bỏ trống, dùng company từ lead
  "company_phone": "0901234567",               // Nếu bỏ trống, dùng phone từ lead
  "company_email": "contact@abc.com",          // Nếu bỏ trống, dùng email từ lead
  "company_address": "123 Nguyễn Huệ, Q.1",
  "opportunity_title": "Dự án ERP Q4/2026",   // Nếu bỏ trống, tự tạo từ tên lead
  "opportunity_value": 150000000,
  "opportunity_stage": "Tiếp cận",
  "opportunity_stage_key": "contact",
  "opportunity_expected_close_date": "2026-12-31",
  "contact_position": "Giám đốc mua hàng"
}
```
Response `201`:
```json
{
  "message": "Lead đã chuyển đổi thành công. Khách hàng #15, Cơ hội #8 được tạo.",
  "result": {
    "lead_id": 42,
    "customer_id": 15,
    "opportunity_id": 8,
    "customer_name": "Công ty TNHH ABC",
    "opportunity_title": "Dự án ERP Q4/2026",
    "contact": { "full_name": "Nguyễn Văn A", "email": "...", "phone": "...", "position": "Giám đốc mua hàng" },
    "converted_at": 1728547200000,
    "activities_migrated": 5
  }
}
```

---

## 🧪 Kiểm thử Tự động

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_convert_to_customer.py -v
```
