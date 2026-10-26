# BUG-QA-002: Chưa khóa tạm thời tài khoản sau 5 lần đăng nhập sai liên tiếp

## 1. Thông tin chung
- **Mã lỗi:** BUG-QA-002
- **Người phát hiện / Kiểm thử:** Đinh Xuân Mạnh (Mã sinh viên: `dtc245200270` - Email: `manhdinh2907@gmail.com`)
- **Vai trò:** Kỹ sư kiểm thử độc lập (Independent QA Engineer)
- **Ngày ghi nhận:** 26/10/2026
- **Phân hệ / API:** Xác thực người dùng (`POST /api/auth/login`)
- **Mức độ ảnh hưởng:** Medium (Tiêu chuẩn bảo mật xác thực - Chống tấn công brute-force dò quét mật khẩu)
- **Tệp kiểm thử tự động tái hiện:** [test_qa_toan_dien.py:test_17](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/tests/test_qa_toan_dien.py#L330)

---

## 2. Điều kiện tiền đề
- Hệ thống Backend đang chạy với CSDL SQLite chuẩn.
- Tài khoản người dùng tồn tại và đang hoạt động trong hệ thống (ví dụ: `nhanvien1`, mật khẩu hợp lệ: `123456`).

---

## 3. Các bước tái hiện
1. Gửi liên tiếp 5 yêu cầu HTTP `POST /api/auth/login` với dữ liệu mật khẩu sai:
   ```json
   {
     "username": "nhanvien1",
     "password": "SaiMatKhau@999"
   }
   ```
2. Quan sát phản hồi ở lần thứ 5 (nhận mã HTTP 401).
3. Gửi tiếp yêu cầu thứ 6 với mật khẩu ĐÚNG:
   ```json
   {
     "username": "nhanvien1",
     "password": "123456"
   }
   ```

---

## 4. Kết quả mong đợi (Expected Result)
- Sau 5 lần nhập sai mật khẩu liên tiếp, tài khoản phải bị khóa tạm thời trong vòng 15 phút.
- Yêu cầu ở lần thứ 6 (kể cả khi nhập đúng mật khẩu) phải bị từ chối với mã lỗi HTTP 401 hoặc 423 (Locked), kèm thông báo rõ ràng:
  *"Tài khoản tạm thời bị khóa trong 15 phút do nhập sai mật khẩu quá 5 lần liên tiếp."*
- Không cấp access_token cho phiên đăng nhập này.

---

## 5. Kết quả thực tế (Actual Result)
- Cả 5 lần gửi mật khẩu sai đều trả về HTTP 401: `{"detail": "Tên đăng nhập hoặc mật khẩu không đúng."}`.
- Ở lần thứ 6 khi gửi mật khẩu đúng, hệ thống vẫn cấp token thành công ngay lập tức (HTTP 200 OK) kèm `access_token`.
- **Nguyên nhân mã nguồn & CSDL:**
  - Kiểm tra cấu trúc CSDL trong `app/schema.sql`: Bảng `users` hoàn toàn không có các cột quản lý số lần thử sai (`failed_login_attempts`) và thời gian khóa (`locked_until`).
  - Kiểm tra mã nguồn `app/common/routes_auth.py`: Hàm `login()` chỉ kiểm tra `check_password_hash` và `is_active`, không có cơ chế tăng bộ đếm số lần sai và không kiểm tra thời hạn khóa tạm thời.
- **Bằng chứng kiểm thử tự động:**
  - Test case `test_17_tai_hien_bug_qa_002_khoa_tai_khoan_sau_5_lan_sai` trong `tests/test_qa_toan_dien.py` ghi nhận trạng thái **FAIL**:
    `AssertionError: 200 == 200 : BUG-QA-002 (CHƯA SỬA): Tài khoản không bị khóa sau 5 lần nhập sai! Lần thứ 6 gửi mật khẩu đúng vẫn đăng nhập thành công (HTTP 200) và nhận access_token.`

---

## 6. Đề xuất khắc phục cho Developer
1. Bổ sung trường vào bảng `users` (`app/schema.sql`):
   - `failed_login_attempts INTEGER NOT NULL DEFAULT 0`
   - `locked_until TEXT`
2. Tại `app/common/routes_auth.py`:
   - Trước khi xác thực mật khẩu, kiểm tra nếu `locked_until` tồn tại và lớn hơn thời gian hiện tại (`clock.now()`) thì từ chối ngay với thông báo khóa 15 phút.
   - Nếu mật khẩu sai: Tăng `failed_login_attempts += 1`. Nếu đạt `>= 5`, gán `locked_until = (clock.now() + timedelta(minutes=15)).isoformat()`.
   - Nếu mật khẩu đúng và chưa bị khóa: Reset `failed_login_attempts = 0`, `locked_until = NULL`, sau đó cấp token như bình thường.
