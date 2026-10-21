# Lead Deduplication System (Backend)

Hệ thống xử lý phát hiện trùng lặp và gộp Lead dành cho nhân viên Marketing.

## 🚀 Tính năng chính
- **Phát hiện trùng lặp:** Tự động kiểm tra trùng email, số điện thoại, tên công ty khi tạo mới lead. Trả về mã lỗi 409 nếu phát hiện trùng.
- **Gộp Lead (Merge):** Gộp lead trùng vào lead chính, tự động di chuyển toàn bộ lịch sử tương tác (LeadHistory) sang lead chính để không mất dữ liệu.
- **Truy vết:** Lưu lại lịch sử gộp trong bảng MergeLog.

## 🛠 Cài đặt & Chạy thử
1. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
2. Từ thư mục gốc repo, cài dependencies và chạy server:
   ```bash
   pip install -r scrum_81_lead_dedup/requirements.txt
   uvicorn scrum_81_lead_dedup.main:app --reload
   ```
3. Truy cập tài liệu API (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 📝 Lưu ý cho triển khai
- Hiện tại hệ thống sử dụng **SQLite**. Để chuyển sang PostgreSQL/MySQL, vui lòng cập nhật `SQLALCHEMY_DATABASE_URL` trong file `database.py`.
