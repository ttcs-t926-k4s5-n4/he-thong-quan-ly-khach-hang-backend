# 📦 Product Catalog & Price List Management System

Hệ thống quản lý danh mục sản phẩm và bảng giá niêm yết, đảm bảo tính thống nhất trong báo giá và bảo mật thông tin giá vốn.

## ✨ Tính năng chính
- **Quản lý Danh mục**: Khai báo chi tiết sản phẩm (Mã, Tên, Loại, Đơn vị tính, Giá niêm yết, Giá sàn).
- **Phân loại Sản phẩm**: Hỗ trợ phân biệt sản phẩm mua một lần và dịch vụ thuê bao.
- **Kiểm soát Giá sàn**: Giá sàn làm căn cứ xác định việc phê duyệt chiết khấu.
- **Bảo mật Giá vốn**: Phân quyền nghiêm ngặt, chỉ Giám đốc kinh doanh mới được xem và sửa giá vốn.
- **Toàn vẹn Dữ liệu**: Chặn xóa sản phẩm đã có trong báo giá, chỉ cho phép chuyển trạng thái sang "Ngừng kinh doanh".

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

## 🔐 Hướng dẫn truy cập quyền Admin (Giám đốc kinh doanh)
Để truy cập các API xem giá vốn hoặc thực hiện thao tác quản trị, bạn cần thêm Header sau vào request:
- **Key**: `X-Role`
- **Value**: `SalesDirector`

## 📂 Cấu trúc thư mục
- `app/`: Mã nguồn Backend chính.
- `tests/`: Các kịch bản kiểm thử tự động.
- `requirements.txt`: Danh sách thư viện.
- `seed.py`: Script khởi tạo dữ liệu mẫu.
