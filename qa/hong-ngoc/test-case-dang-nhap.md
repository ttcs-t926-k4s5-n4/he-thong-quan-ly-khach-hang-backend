# KIỂM THỬ ĐĂNG NHẬP VÀ XÁC THỰC

- Người thực hiện: Vy Thị Hồng Ngọc.
- Phân loại: công việc phối hợp và kiểm thử bổ sung.
- Bản xuất Jira cá nhân chưa có issue đăng nhập được giao tương ứng.
- Không đồng nhất đăng nhập với SCRUM-148 về khóa tài khoản
  khi nhân viên nghỉ và bàn giao dữ liệu.

## 1. Kết quả thủ công ngày 03/10/2026

### Phạm vi

- Đăng nhập.
- Thông báo sai thông tin.
- Khóa tạm sau 5 lần sai liên tiếp.

### Kết quả

- 3 trường hợp: 2 đạt, 1 chưa đạt.
- Tài khoản chưa bị khóa 15 phút sau 5 lần sai.
- Chưa có mã test chi tiết cho ba trường hợp.
- Chưa có retest xác nhận đã khắc phục.

Yêu cầu đối chiếu:
- Đăng nhập đúng vào trang theo vai trò.
- Sai thông tin có thông báo chung.
- Không tiết lộ email tồn tại hay không.
- Khóa tạm 15 phút sau 5 lần sai.

Không tự suy ra từng tiêu chí đã đạt
từ số liệu tổng hợp 2/3.

## 2. Tài liệu hóa test tự động có sẵn

Nguồn: tests/test_chung.py.
Log: ket-qua-test-chung.txt.

Bốn tình huống dưới đây nằm trong hai hàm test,
không tính thành bốn test tự động mới.

| Mã | Tình huống | Kết quả mong đợi trong bộ test | Kết quả |
|---|---|---|---|
| AUTH-01 | Đăng nhập đúng với tài khoản mẫu | HTTP 200; thông báo đăng nhập thành công; nhãn vai trò đúng | Đạt theo log hàm test |
| AUTH-02 | Đăng nhập sai mật khẩu | HTTP 401; thông báo Tên đăng nhập hoặc mật khẩu không đúng | Đạt theo log hàm test |
| AUTH-03 | Truy cập API không gửi token | HTTP 401; thông báo chưa đăng nhập | Đạt theo log hàm test |
| AUTH-04 | Truy cập API với token abc | HTTP 401; thông báo token không hợp lệ | Đạt theo log hàm test |

Hàm test tương ứng:
- test_dang_nhap_thanh_cong_va_that_bai.
- test_chua_dang_nhap_va_token_sai.

## 3. Ba test QA bổ sung

Nguồn: tests/test_qa_hong_ngoc_login.py.
Log: ket-qua-login-bo-sung.txt.

| Mã | Hàm test | Dữ liệu | Mong đợi | Kết quả |
|---|---|---|---|---|
| AUTH-05 | test_thieu_ten_dang_nhap | {"password":"123456"} | HTTP 422; lỗi bắt buộc username; không có access_token hoặc user | Đạt theo log |
| AUTH-06 | test_thieu_mat_khau | {"username":"nhanvien1"} | HTTP 422; lỗi bắt buộc password; không có access_token hoặc user | Đạt theo log |
| AUTH-07 | test_json_rong_thieu_ca_hai_truong | {} | HTTP 422; lỗi bắt buộc cả hai trường; không có access_token hoặc user | Đạt theo log |

Log bổ sung ghi 10 test đạt:
- 7 test_chung.
- 3 test mới.

Chỉ tăng số test khác nhau thêm 3.
Không cộng lại 7 test_chung.

## 4. Giới hạn kết quả

- Ba test thiếu trường không phải ba trường hợp thủ công ngày 03/10.
- Không gửi trường khác với gửi chuỗi rỗng hoặc chỉ có khoảng trắng.
- Chưa có kết quả riêng cho token hết hạn,
  đăng xuất rồi dùng lại token và giới hạn tần suất.
- Có ghi nhận lỗi khóa tạm ngày 03/10,
  nhưng chưa có retest xác nhận đã sửa.
- Log của bản backend kiểm tra không tự chứng minh
  mọi bản triển khai CRM khác cũng có cùng kết quả.

## 5. Minh chứng cần hoàn thiện

- Mã test và nội dung ba trường hợp thủ công.
- Ảnh/log lỗi khóa tạm.
- Phiên bản và môi trường ngày kiểm thử.
- Mã lỗi Jira nếu có.
- Kết quả retest sau sửa.
