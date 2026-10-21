# 🏢 Company Hierarchy Management System

Hệ thống quản lý quan hệ Công ty Mẹ - Công ty Con, cho phép theo dõi cấu trúc tập đoàn và tổng hợp giá trị hợp đồng toàn nhóm.

## ✨ Tính năng chính
- **Quản lý Phân cấp**: Thiết lập quan hệ Mẹ - Con giữa các khách hàng (Sử dụng mô hình Self-referencing).
- **Tính toán Tổng giá trị Nhóm**: Tự động tính tổng giá trị hợp đồng của công ty mẹ và TẤT CẢ các công ty con, cháu (đệ quy) trong tập đoàn.
- **Ngăn chặn Vòng lặp**: Logic bảo vệ không cho phép một công ty làm mẹ của chính nó hoặc tạo ra vòng lặp vô tận trong cây phân cấp.

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
- `seed.py`: Script khởi tạo dữ liệu mẫu để demo cây phân cấp.
