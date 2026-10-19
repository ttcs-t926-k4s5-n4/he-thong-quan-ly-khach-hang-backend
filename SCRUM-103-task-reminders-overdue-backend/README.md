# SCRUM-103: Nhắc việc sắp đến hạn & Xử lý việc quá hạn (Task Reminders & Overdue) — Backend Python

## 📌 1. User Story & Tổng quan

> **"Là Nhân viên kinh doanh, tôi muốn được nhắc việc sắp đến hạn và việc quá hạn, để không để công việc bị bỏ quên vì bận chạy thương vụ khác."**

Tính năng này triển khai cơ chế tự động theo dõi tiến độ và cảnh báo thời hạn công việc:
- Quản lý công việc (tasks) liên kết với khách hàng, cơ hội kinh doanh và người phụ trách.
- Xác định công việc sắp đến hạn dựa trên các mốc nhắc trước linh hoạt (`24h`, `1h`...).
- Xác định công việc quá hạn (`due_date < now` và chưa hoàn thành/hủy).
- Tự động tạo thông báo trong ứng dụng (`notifications`), chống tạo trùng lặp qua ràng buộc Unique Deduplication.
- Cung cấp API báo cáo thống kê công việc quá hạn của từng thành viên cho Trưởng nhóm/Admin.
- Tác vụ nền (Background Worker) định kỳ quét hạn công việc mà không sinh nhiều scheduler ngoài ý muốn khi chạy reload.

---

## 📂 2. Cấu trúc thư mục Feature

```
SCRUM-103-task-reminders-overdue-backend/
├── README.md                                    ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_103_task_reminders_overdue.sql    ← Migration CSDL: dbo.tasks, dbo.notifications, dbo.task_reminder_settings
└── backend/
    ├── app/
    │   ├── tasks_reminders.py                   ← ★ Module chính: Quản lý công việc, nhắc hạn & thông báo
    │   ├── routes.py                            ← REST API Endpoints (/tasks, /notifications, /teams)
    │   └── ...                                  ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_task_reminders_overdue.py      ← ★ Bộ kiểm thử tự động toàn diện (11 test cases)
```

---

## 🗄️ 3. Database Schema

### 1. Bảng `dbo.tasks`
Lưu trữ thông tin công việc, phân công và thời hạn:
- `id`: INT IDENTITY PRIMARY KEY
- `title`: NVARCHAR(250) NOT NULL
- `assigned_to`: INT NOT NULL (FK users)
- `customer_id`: INT NULL (FK customers)
- `opportunity_id`: INT NULL (FK opportunities)
- `due_date`: BIGINT NOT NULL (epoch ms)
- `priority`: NVARCHAR(50) DEFAULT 'medium'
- `status`: NVARCHAR(50) DEFAULT 'pending'

### 2. Bảng `dbo.notifications`
Lưu trữ thông báo trong ứng dụng cho người dùng:
- `id`: BIGINT IDENTITY PRIMARY KEY
- `user_id`: INT NOT NULL (FK users)
- `title`: NVARCHAR(250) NOT NULL
- `message`: NVARCHAR(MAX) NOT NULL
- `type`: NVARCHAR(50) NOT NULL ('task_due_soon', 'task_overdue')
- `reference_type`: NVARCHAR(50) ('task')
- `reference_id`: INT NULL
- `reminder_milestone`: NVARCHAR(50) ('24h', '1h', 'overdue')
- `is_read`: BIT DEFAULT 0

---

## 📡 4. Chi tiết API Endpoints

### 1. `GET /api/tasks/reminders`
- **Mô tả**: Lấy danh sách việc sắp đến hạn của người dùng hiện tại (còn dưới 24h hoặc theo mốc cấu hình).
- **Response mẫu (200 OK)**:
```json
{
  "total": 1,
  "reminders": [
    {
      "id": 1,
      "title": "Gửi báo giá hợp đồng",
      "due_date": 1729350000000,
      "hours_left": 3.5,
      "priority": "high",
      "status": "pending",
      "customer_name": "Công ty TNHH Nam Việt",
      "opportunity_title": "Dự án CRM 2026"
    }
  ]
}
```

### 2. `GET /api/tasks/overdue`
- **Mô tả**: Lấy danh sách việc quá hạn của người dùng hiện tại để hiển thị nổi bật trên Dashboard.
- **Response mẫu (200 OK)**:
```json
{
  "total": 1,
  "overdue_tasks": [
    {
      "id": 2,
      "title": "Gọi lại xác nhận lịch hẹn",
      "due_date": 1729320000000,
      "overdue_hours": 5.2,
      "priority": "medium",
      "status": "in_progress"
    }
  ]
}
```

### 3. `GET /api/notifications`
- **Mô tả**: Lấy danh sách thông báo của người dùng với phân trang và lọc chưa đọc (`?unread_only=true&page=1&per_page=20`).

### 4. `PATCH /api/notifications/<id>/read`
- **Mô tả**: Đánh dấu thông báo đã đọc.

### 5. `GET /api/teams/overdue-summary`
- **Mô tả**: Thống kê số lượng việc quá hạn theo từng thành viên (Trưởng nhóm / Admin).
- **Phân quyền**: Nhân viên thông thường bị từ chối với mã 403.
- **Response mẫu (200 OK)**:
```json
{
  "total_members": 2,
  "members": [
    {
      "user_id": 5,
      "full_name": "Trần Văn B",
      "email": "b.tran@company.vn",
      "group_name": "Nhóm Kinh doanh 1",
      "overdue_count": 2,
      "overdue_tasks": [...]
    }
  ]
}
```

### 6. `GET` & `PUT /api/tasks/reminder-settings`
- **Mô tả**: Lấy và cập nhật mốc nhắc trước hạn động (`{"milestones": ["48h", "2h", "30m"]}`).
