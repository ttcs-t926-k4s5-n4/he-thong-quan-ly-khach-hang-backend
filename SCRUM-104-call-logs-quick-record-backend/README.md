# SCRUM-104: Ghi nhanh kết quả cuộc gọi (Call Logs & Mobile Quick Record) — Backend Python

## 📌 1. User Story & Tổng quan

> **"Là Nhân viên kinh doanh, tôi muốn ghi nhanh kết quả cuộc gọi ngay trên điện thoại, để ghi lại khi còn nhớ thay vì để tối về quên mất."**

Tính năng này cung cấp RESTful API phục vụ giao diện mobile/web thao tác nhanh:
- Ghi nhanh kết quả cuộc gọi với khách hàng (`Đã liên hệ thành công`, `Không nghe máy`, `Hẹn gọi lại`, `Khách hàng quan tâm`...).
- **Tự động liên kết Cơ hội mở gần nhất**: nếu nhân viên không chọn cơ hội, hệ thống tự động tìm cơ hội đang mở mới nhất của khách hàng mà nhân viên có quyền truy cập.
- **Ràng buộc toàn vẹn**: nếu người dùng chủ động chọn cơ hội, backend kiểm tra chặt chẽ cơ hội đó phải thuộc đúng khách hàng đã chọn.
- **Lịch gọi lại (Callback)**: hỗ trợ đặt lịch gọi lại và tự động tạo công việc trong module công việc (`tasks`), ngăn tạo trùng lặp khi client gửi lại request.
- **Lịch sử cuộc gọi**: tra cứu lịch sử cuộc gọi theo khách hàng với phân trang và lọc đa tiêu chí.

---

## 📂 2. Cấu trúc thư mục Feature

```
SCRUM-104-call-logs-quick-record-backend/
├── README.md                                    ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_104_call_logs.sql                 ← Migration CSDL: bảng dbo.call_logs
└── backend/
    ├── app/
    │   ├── call_logs.py                         ← ★ Module chính: Ghi nhanh cuộc gọi & liên kết cơ hội
    │   ├── tasks_reminders.py                   ← Module công việc & lịch gọi lại
    │   ├── routes.py                            ← REST API Endpoints (/calls, /customers/<id>/calls)
    │   └── ...                                  ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_call_logs.py                   ← ★ Bộ kiểm thử tự động toàn diện (13 test cases)
```

---

## 🗄️ 3. Database Schema (`dbo.call_logs`)

```sql
CREATE TABLE dbo.call_logs (
    id                BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
    customer_id       INT            NOT NULL,
    opportunity_id    INT            NULL,
    user_id           INT            NOT NULL,
    call_result       NVARCHAR(100)  NOT NULL,
    notes             NVARCHAR(1000) NULL,
    called_at         BIGINT         NOT NULL,
    callback_at       BIGINT         NULL,
    callback_task_id  INT            NULL,
    created_at        BIGINT         NOT NULL,
    updated_at        BIGINT         NOT NULL,
    CONSTRAINT FK_call_logs_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE,
    CONSTRAINT FK_call_logs_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id),
    CONSTRAINT FK_call_logs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
    CONSTRAINT FK_call_logs_task FOREIGN KEY (callback_task_id) REFERENCES dbo.tasks(id)
);
```

---

## 📡 4. Chi tiết API Endpoints

### 1. `POST /api/calls`
- **Mô tả**: Tạo bản ghi cuộc gọi nhanh từ mobile / web.
- **Request Body**:
```json
{
  "customer_id": 5,
  "call_result": "interested",
  "notes": "Khách hàng rất quan tâm đến giải pháp CRM, đề nghị demo vào tuần sau.",
  "callback_at": 1729420800000
}
```
*(Không truyền `opportunity_id` → Hệ thống tự động tìm và gán cơ hội mở gần nhất của khách hàng)*

- **Response mẫu (201 Created)**:
```json
{
  "message": "Ghi nhận kết quả cuộc gọi thành công.",
  "call_log": {
    "id": 1,
    "customer_id": 5,
    "customer_name": "Công ty TNHH Nam Việt",
    "opportunity_id": 12,
    "opportunity_title": "Dự án CRM 2026",
    "user_id": 2,
    "caller_name": "Nguyễn Văn A",
    "call_result": "interested",
    "call_result_label": "Khách hàng quan tâm",
    "notes": "Khách hàng rất quan tâm đến giải pháp CRM, đề nghị demo vào tuần sau.",
    "called_at": 1729334400000,
    "callback_at": 1729420800000,
    "callback_task_id": 8,
    "created_at": 1729334400000,
    "updated_at": 1729334400000
  }
}
```

### 2. `GET /api/customers/<customer_id>/calls`
- **Mô tả**: Lấy lịch sử cuộc gọi của khách hàng với phân trang và bộ lọc.
- **Query params**: `page`, `per_page`, `call_result`, `from_date`, `to_date`.
- **Response mẫu (200 OK)**:
```json
{
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "customer_id": 5,
      "caller_name": "Nguyễn Văn A",
      "call_result": "interested",
      "call_result_label": "Khách hàng quan tâm",
      "opportunity_title": "Dự án CRM 2026",
      "notes": "Khách hàng rất quan tâm...",
      "called_at": 1729334400000
    }
  ]
}
```

### 3. `GET /api/calls/<call_id>`
- **Mô tả**: Xem chi tiết bản ghi cuộc gọi (người gọi hoặc quản lý).

### 4. `PATCH /api/calls/<call_id>`
- **Mô tả**: Cập nhật ghi chú hoặc kết quả cuộc gọi (chỉ người tạo hoặc quản lý).
