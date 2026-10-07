# 🚀 Sales Common Categories System

Hệ thống quản lý danh mục dùng chung cho khối Kinh doanh, hỗ trợ chuẩn hóa dữ liệu Ngành nghề, Quy mô doanh nghiệp, Nguồn Lead và Loại hoạt động để phục vụ báo cáo tổng hợp.

## ✨ Tính năng chính
- **Quản lý Linh hoạt**: Tạo, cập nhật và quản lý các loại danh mục và giá trị chi tiết.
- **Sắp xếp Thứ tự**: Hỗ trợ trường `display_order` để tùy chỉnh thứ tự hiển thị trên giao diện.
- **Bảo vệ Dữ liệu (Data Integrity)**: Tự động chặn xóa các giá trị đang được tham chiếu bởi dữ liệu thực tế (ví dụ: Lead) để tránh gây lỗi hệ thống.
- **API chuẩn RESTful**: Xây dựng trên FastAPI với hiệu năng cao và tài liệu tự động.

## 🛠 Cài đặt & Chạy ứng dụng

### 1. Yêu cầu hệ thống
- Python 3.9+
- pip (Python package manager)

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng
```bash
uvicorn app.main:app --reload
```
Sau khi chạy, bạn có thể truy cập:
- **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Alternative Docs (ReDoc)**: `http://127.0.0.1:8000/redoc`

## 🧪 Kiểm thử & Demo

### Đổ dữ liệu mẫu (Seed Data)
Để nhanh chóng xem kết quả mà không cần nhập tay, hãy chạy file seed:
```bash
python seed.py
```

### Chạy Unit Test
Để kiểm tra tính đúng đắn của logic (đặc biệt là tính năng chặn xóa), hãy chạy lệnh:
```bash
pytest
```

## 📂 Cấu trúc thư mục
- `app/`: Chứa toàn bộ mã nguồn xử lý Backend.
- `tests/`: Các kịch bản kiểm thử tự động.
- `requirements.txt`: Danh sách thư viện phụ thuộc.
- `seed.py`: Script khởi tạo dữ liệu mẫu cho demo.
