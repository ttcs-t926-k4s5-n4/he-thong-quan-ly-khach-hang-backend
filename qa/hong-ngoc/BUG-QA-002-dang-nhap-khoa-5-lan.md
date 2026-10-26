# BUG-QA-002: Chưa khóa tạm thời tài khoản sau 5 lần đăng nhập sai liên tiếp

## 1. Thông tin chung
- **Mã lỗi:** BUG-QA-002
- **Người phát hiện:** QA Team
- **Ngày ghi nhận:** 26/10/2026
- **Phân hệ / API:** Xác thực người dùng (`POST /api/auth/login`)
- **Mức độ ảnh hưởng:** Medium (Tiêu chuẩn bảo mật - Ngăn chặn tấn công Brute-force dò mật khẩu)

---

## 2. Điều kiện tiền đề
- Hệ thống Backend đang chạy với CSDL SQLite chuẩn.
- Tài khoản người dùng tồn tại trong hệ thống (ví dụ: `nhanvien1`).

---

## 3. Các bước tái hiện
1. Gửi liên tiếp 5 yêu cầu HTTP `POST /api/auth/login` với dữ liệu:
   ```json
   {
     "username": "nhanvien1",
     "password": "SaiMatKhau@999"
   }
   ```
2. Quan sát phản hồi ở lần thứ 5.
3. Gửi tiếp yêu cầu thứ 6 với mật khẩu đúng:
   ```json
   {
     "username": "nhanvien1",
     "password": "123456"
   }
   ```

---

## 4. Kết quả mong đợi
- Sau 5 lần nhập sai mật khẩu liên tiếp, tài khoản phải bị khóa tạm thời trong 15 phút.
- Yêu cầu ở lần thứ 6 (kể cả khi nhập đúng mật khẩu) phải bị từ chối với mã lỗi HTTP 401 hoặc 423 (Locked), thông báo:
  *"Tài khoản tạm thời bị khoá trong 15 phút do nhập sai mật khẩu quá 5 lần liên tiếp."*

---

## 5. Kết quả thực tế
- Cả 5 lần gửi mật khẩu sai đều chỉ trả về HTTP 401: `{"detail": "Tên đăng nhập hoặc mật khẩu không đúng."}`.
- Lần thứ 6 gửi mật khẩu đúng thì hệ thống vẫn cấp token thành công ngay lập tức (HTTP 200).
- Kiểm tra cấu trúc CSDL trong `app/schema.sql`: Bảng `users` không có các trường quản lý số lần thử sai và thời gian khóa (`failed_login_attempts`, `locked_until`).
- Kiểm tra mã nguồn `app/common/routes_auth.py`: Không có logic đếm số lần sai và chặn đăng nhập tạm thời.

---

## 6. Đề xuất xử lý cho Developer
1. Bổ sung trường vào bảng `users`:
   - `failed_login_attempts INTEGER NOT NULL DEFAULT 0`
   - `locked_until TEXT`
2. Tại `routes_auth.py`:
   - Trước khi kiểm tra mật khẩu, kiểm tra nếu `locked_until` tồn tại và lớn hơn thời gian hiện tại (`clock.now()`) thì từ chối ngay.
   - Nếu mật khẩu sai: Tăng `failed_login_attempts += 1`. Nếu đạt >= 5, đặt `locked_until = clock.now() + timedelta(minutes=15)`.
   - Nếu mật khẩu đúng: Reset `failed_login_attempts = 0`, `locked_until = NULL`.
