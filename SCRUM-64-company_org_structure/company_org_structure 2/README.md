# 🏢 Company Org Structure Management System

Hệ thống quản lý cơ cấu tổ chức kinh doanh, hỗ trợ phân cấp nhóm (cây tổ chức) và định nghĩa phạm vi dữ liệu (data scope) cho cấp quản lý.

## ✨ Tính năng chính
- **Cấu trúc Nhóm dạng Cây**: Hỗ trợ khai báo nhóm mẹ - nhóm con, cho phép tạo ra nhiều cấp bậc quản lý.
- **Quản lý Nhân sự**: Mỗi nhân viên thuộc đúng một nhóm tại một thời điểm, mỗi nhóm có một trưởng nhóm (Team Lead) duy nhất.
- **Quản lý Khu vực**: Khai báo các khu vực địa lý và gán khu vực cho từng nhóm kinh doanh.
- **Phân quyền Phạm vi Dữ liệu (Data Scope)**: Tự động tính toán và trả về danh sách tất cả các nhóm con và nhân viên thuộc quyền quản lý của một Trưởng nhóm (tính đệ quy toàn bộ cây bên dưới).

## 🛠 Cài đặt & Chạy ứng dụng

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng
```bash
uvicorn app.main:app --reload
```
Truy cập tài liệu API tại: `http://127.0.0.1:8000/docs`

## 📂 Cấu trúc thư mục
- `app/`: Mã nguồn Backend.
- `requirements.txt`: Danh sách thư viện.
- `seed.py`: Script khởi tạo dữ liệu mẫu cho cây tổ chức.
