# Sprint 1 — Hệ thống Quản lý Bán hàng (CRM)

Dự án tích hợp toàn bộ **10 User Stories của Sprint 1** vào một project duy nhất.

## Cấu trúc

```
sprint1/
├── backend/          ← Python Flask API (port 5000)
├── frontend/         ← React + Vite (port 5173)
├── database/         ← SQL schema tổng hợp
└── README.md
```

## Yêu cầu cài đặt

| Phần mềm | Phiên bản |
|----------|-----------|
| Python   | ≥ 3.11    |
| Node.js  | ≥ 20      |
| SQL Server | 2019+ (hoặc Express) |
| ODBC Driver 18 for SQL Server | [Tải tại đây](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) |

---

## 🗄️ Bước 1 — Tạo Database

1. Mở **SQL Server Management Studio (SSMS)**
2. Tạo database mới: `crm_db`
3. Chạy file SQL:
   ```
   database/sprint1_full.sql
   ```

---

## ⚙️ Bước 2 — Cấu hình Backend

```powershell
cd backend

# Copy file .env
Copy-Item .env.example .env

# Mở .env và chỉnh các thông số SQL Server của bạn:
# SQL_SERVER_HOST=localhost
# SQL_SERVER_USER=sa
# SQL_SERVER_PASSWORD=YourPassword
```

### Tạo virtual environment & cài dependencies

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Seed dữ liệu mẫu

```powershell
python seed_users.py
```

Lệnh này tạo 3 tài khoản mẫu:

| Role     | Email                   | Mật khẩu       |
|----------|-------------------------|----------------|
| admin    | admin@company.vn        | Admin@123      |
| manager  | manager@company.vn      | Manager@123    |
| employee | employee@company.vn     | Employee@123   |

### Chạy backend

```powershell
python run.py
```

Backend chạy tại: **http://127.0.0.1:5000**

---

## 🎨 Bước 3 — Chạy Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend chạy tại: **http://localhost:5173**

---

## 🧪 Kiểm tra API

```powershell
# Health check
Invoke-RestMethod http://127.0.0.1:5000/api/health

# Đăng nhập
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/login `
  -Method POST -ContentType "application/json" `
  -Body '{"email":"admin@company.vn","password":"Admin@123"}'
```

---

## 📋 User Stories đã tích hợp

| Story | Tính năng | Status |
|-------|-----------|--------|
| S1-01 | Đăng nhập email/password, chống lộ thông tin | ✅ Done |
| S1-02 | Session management — gia hạn 15 phút tự động | ✅ Done |
| S1-03 | Quên mật khẩu, link reset qua email 30 phút  | ✅ Done |
| S1-04 | Đổi mật khẩu khi đang đăng nhập, thu hồi session khác | ✅ Done |
| S1-05 | Phân quyền dữ liệu theo vai trò (admin/manager/employee) | ✅ Done |
| S1-06 | Menu ẩn/hiện theo vai trò                   | ✅ Done |
| S1-07 | Thông báo lỗi rõ ràng tiếng Việt            | ✅ Done |
| S1-08 | Quản lý tài khoản: tạo, tìm, lọc, phân trang | ✅ Done |
| S1-09 | Quản lý vai trò & nhóm kinh doanh            | ✅ Done |
| S1-10 | Khóa tài khoản sau 5 lần đăng nhập sai       | ✅ Done |

---

## 🔧 Cấu hình Email (tùy chọn)

Mặc định (`MAIL_BACKEND=console`) — email được in ra terminal.

Để gửi email thật, chỉnh `.env`:
```env
MAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_STARTTLS=true
```

---

## 📁 Endpoints API

| Method | Path | Mô tả |
|--------|------|-------|
| GET  | /api/health | Health check |
| POST | /api/auth/login | Đăng nhập |
| GET  | /api/auth/me | Lấy thông tin session |
| POST | /api/auth/logout | Đăng xuất |
| POST | /api/auth/forgot-password | Yêu cầu reset password |
| GET  | /api/auth/reset-password/{token} | Kiểm tra token reset |
| POST | /api/auth/reset-password/{token} | Đặt lại mật khẩu |
| POST | /api/account/change-password | Đổi mật khẩu |
| GET  | /api/users | Danh sách user (admin) |
| POST | /api/users | Tạo user mới (admin) |
| PUT  | /api/users/{id} | Cập nhật user (admin) |
| POST | /api/users/activate | Kích hoạt tài khoản |
