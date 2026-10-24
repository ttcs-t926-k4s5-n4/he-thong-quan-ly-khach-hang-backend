# Test case đăng nhập và xác thực API

Người phân tích, lập tài liệu: Vy Thị Hồng Ngọc — QA
Nguồn: tests/test_chung.py
Minh chứng thực thi: ket-qua-test-chung.txt
Phiên bản được kiểm thử: xem phien-ban-kiem-thu.txt

## Phạm vi
Phân tích 4 tình huống từ 2 hàm test tự động có sẵn:
- test_dang_nhap_thanh_cong_va_that_bai
- test_chua_dang_nhap_va_token_sai

Đây là tài liệu hóa bộ test hiện có, không phải bổ sung
4 test tự động mới. Kết quả dựa trên log lần chạy đã lưu.

## Điều kiện chung
- Môi trường kiểm thử được khởi tạo bằng CRMTestCase.
- Có dữ liệu tài khoản mẫu nhanvien1, mật khẩu 123456.
- Chỉ sử dụng tài khoản mẫu trong môi trường kiểm thử.

## AUTH-01: Đăng nhập đúng thông tin

Dữ liệu:
{"username":"nhanvien1","password":"123456"}

Các bước:
1. Gửi POST /api/auth/login với dữ liệu trên.
2. Kiểm tra mã HTTP và nội dung JSON trả về.

Kết quả mong đợi theo bộ test:
- HTTP 200.
- message chứa "Đăng nhập thành công".
- user.role_label bằng "Nhân viên kinh doanh".

Hàm test đối chiếu:
test_dang_nhap_thanh_cong_va_that_bai

Kết quả ghi nhận:
Đạt theo log của hàm test tương ứng.

## AUTH-02: Đăng nhập sai mật khẩu

Dữ liệu:
{"username":"nhanvien1","password":"sai"}

Các bước:
1. Trong hàm test có sẵn, tình huống này chạy sau AUTH-01.
2. Gửi POST /api/auth/login với mật khẩu sai.
3. Kiểm tra mã HTTP và thông báo lỗi.

Kết quả mong đợi theo bộ test:
- HTTP 401.
- detail bằng "Tên đăng nhập hoặc mật khẩu không đúng."

Hàm test đối chiếu:
test_dang_nhap_thanh_cong_va_that_bai

Kết quả ghi nhận:
Đạt theo log của hàm test tương ứng.

## AUTH-03: Truy cập API khi không gửi token

Các bước:
1. Gửi GET /api/opportunities, không gửi thông tin xác thực.
2. Kiểm tra mã HTTP và thông báo lỗi.

Kết quả mong đợi theo bộ test:
- HTTP 401.
- detail chứa "Bạn chưa đăng nhập".

Hàm test đối chiếu:
test_chua_dang_nhap_va_token_sai

Kết quả ghi nhận:
Đạt theo log của hàm test tương ứng.

## AUTH-04: Truy cập API với token không hợp lệ

Các bước:
1. Gửi GET /api/opportunities.
2. Đặt header Authorization: Bearer abc.
3. Kiểm tra mã HTTP và thông báo lỗi.

Kết quả mong đợi theo bộ test:
- HTTP 401.
- detail bằng "Token đăng nhập không hợp lệ."

Hàm test đối chiếu:
test_chua_dang_nhap_va_token_sai

Kết quả ghi nhận:
Đạt theo log của hàm test tương ứng.

## Giới hạn và khoảng trống cần kiểm thử thêm
Hai hàm test trên chưa chứng minh các tình huống:
- Bỏ trống tên đăng nhập hoặc mật khẩu.
- Token hết hạn.
- Đăng xuất và sử dụng lại token.
- Khóa tài khoản sau nhiều lần nhập sai.
- Giới hạn tần suất đăng nhập.

Các mục trên là đề xuất kiểm thử thêm, chưa có kết quả
thực thi trong tài liệu này.

## Lệnh chạy lại hai hàm test
.venv\Scripts\python.exe -m unittest tests.test_chung.TestChung.test_dang_nhap_thanh_cong_va_that_bai tests.test_chung.TestChung.test_chua_dang_nhap_va_token_sai -v
## Bổ sung kết quả kiểm thử dữ liệu đăng nhập

Nguồn: tests/test_qa_hong_ngoc_login.py.
Minh chứng: ket-qua-login-bo-sung.txt.

| Mã | Tình huống | Dữ liệu gửi | Kết quả mong đợi | Kết quả theo log |
|---|---|---|---|---|
| AUTH-05 | Thiếu tên đăng nhập | {"password":"123456"} | HTTP 422; lỗi bắt buộc username; không cấp token hoặc user | Đạt |
| AUTH-06 | Thiếu mật khẩu | {"username":"nhanvien1"} | HTTP 422; lỗi bắt buộc password; không cấp token hoặc user | Đạt |
| AUTH-07 | Thiếu cả hai trường | {} | HTTP 422; báo thiếu username và password; không cấp token hoặc user | Đạt |

Đây là 3 test tự động bổ sung của QA.
Log gồm 10 test đạt: 3 test mới và 7 test_chung.
Không cộng 7 test_chung hai lần khi tổng hợp.

Phân biệt:
- Không gửi trường: đã có kết quả 3 test bổ sung phía trên.
- Gửi chuỗi rỗng hoặc chỉ chứa khoảng trắng: chưa có kết quả riêng trong tài liệu này.
- Token hết hạn, đăng xuất rồi dùng lại token, khóa sau nhiều lần sai
  và giới hạn tần suất: vẫn cần bổ sung minh chứng thực thi.
