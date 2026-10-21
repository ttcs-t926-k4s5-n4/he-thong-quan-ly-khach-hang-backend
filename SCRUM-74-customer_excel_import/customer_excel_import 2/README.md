# 📥 Customer Bulk Import System (from Excel)

Hệ thống hỗ trợ nhập danh sách khách hàng hàng loạt từ file Excel, tích hợp cơ chế xem trước, báo lỗi theo dòng và phát hiện trùng lặp.

## ✨ Tính năng chính
- **Tải Tệp Mẫu**: Cung cấp file Excel chuẩn để người dùng nhập liệu đúng định dạng.
- **Xem trước (Preview)**: Phân tích file Excel và trả về danh sách các dòng cùng trạng thái:
    - `valid`: Dữ liệu hợp lệ, sẵn sàng nhập.
    - `duplicate`: Trùng với khách hàng đã có trong hệ thống (dựa trên Mã số thuế hoặc Tên tương đồng).
    - `error`: Dữ liệu sai hoặc thiếu (ví dụ: thiếu Tên).
- **Nhập có chọn lọc**: Người dùng có thể chọn bỏ qua các dòng trùng/lỗi và chỉ nhập những dòng hợp lệ.
- **Đối soát thông minh**: Sử dụng thuật toán Fuzzy Matching để tìm kiếm khách hàng trùng tên dù cách viết khác nhau.

## 🛠 Cài đặt & Chạy ứng dụng

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Tạo file mẫu (Template)
Trước khi chạy app, hãy tạo file mẫu:
```bash
python create_template.py
```

### 3. Chạy ứng dụng
```bash
uvicorn app.main:app --reload
```
Truy cập API Docs tại: `http://127.0.0.1:8000/docs`

## 🚀 Luồng hoạt động (Workflow)
1. **Bước 1**: Gọi `GET /import/template` để tải file Excel mẫu.
2. **Bước 2**: Người dùng nhập dữ liệu vào file $\rightarrow$ Gọi `POST /import/preview` (Upload file).
3. **Bước 3**: Frontend hiển thị danh sách các dòng cùng trạng thái (Valid/Duplicate/Error).
4. **Bước 4**: Người dùng chọn các dòng muốn nhập $\rightarrow$ Gọi `POST /import/confirm` (Gửi danh sách index các dòng).

## 📂 Cấu trúc thư mục
- `app/`: Mã nguồn Backend.
- `templates/`: Chứa file mẫu `.xlsx`.
- `requirements.txt`: Danh sách thư viện (Pandas, Openpyxl, TheFuzz).
- `create_template.py`: Script tạo file mẫu.
