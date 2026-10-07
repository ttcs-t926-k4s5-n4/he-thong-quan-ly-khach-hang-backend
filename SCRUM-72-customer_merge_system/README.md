# 👥 Customer Duplicate Merge System

Hệ thống phát hiện và gộp khách hàng trùng lặp, ngăn chặn việc nhiều nhân viên cùng tiếp cận một công ty mà không biết nhau.

## ✨ Tính năng chính
- **Phát hiện Trùng lặp Thông minh**:
    - Đối soát chính xác Mã số thuế (Tax ID).
    - Đối soát chính xác Website.
    - Đối soát mờ (Fuzzy Match) Tên công ty với ngưỡng tương đồng 80%.
- **So sánh chi tiết**: Cung cấp dữ liệu đầy đủ (Liên hệ, Cơ hội, Hoạt động) để Trưởng nhóm so sánh trước khi quyết định gộp.
- **Gộp dữ liệu Toàn diện**: Di chuyển toàn bộ lịch sử tương tác từ bản ghi trùng sang bản ghi chính, đảm bảo không mất dữ liệu.
- **Phân quyền Nghiêm ngặt**: Chỉ người có Role `TeamLead` mới có quyền thực hiện lệnh gộp.

## 🛠 Cài đặt & Chạy ứng dụng

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng
```bash
uvicorn app.main:app --reload
```
Truy cập API Docs: `http://127.0.0.1:8000/docs`

## 🔐 Hướng dẫn vận hành quyền Trưởng nhóm
Để thực hiện gộp khách hàng, bạn cần thêm Header sau vào request:
- **Key**: `X-Role`
- **Value**: `TeamLead`

## 📂 Cấu trúc thư mục
- `app/`: Mã nguồn Backend (FastAPI + SQLAlchemy).
- `tests/`: Kịch bản kiểm thử Unit Test.
- `requirements.txt`: Danh sách thư viện (bao gồm `thefuzz` để xử lý trùng tên).
- `seed.py`: Script tạo dữ liệu mẫu để test tính năng phát hiện trùng.
