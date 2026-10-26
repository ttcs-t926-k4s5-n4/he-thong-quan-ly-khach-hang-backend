# BUG-QA-003: Chưa có cơ chế thu hồi token sau khi đăng xuất (Yêu cầu S1-02)

## 1. Thông tin chung
- **Mã lỗi:** BUG-QA-003 (Liên quan yêu cầu nghiệp vụ S1-02)
- **Người phát hiện / Kiểm thử:** Đinh Xuân Mạnh (Mã sinh viên: `dtc245200270` - Email: `manhdinh2907@gmail.com`)
- **Vai trò:** Kỹ sư kiểm thử độc lập (Independent QA Engineer)
- **Ngày ghi nhận:** 26/10/2026
- **Phân hệ / API:** Xác thực và quản lý phiên làm việc (`POST /api/auth/logout`, `GET /api/auth/me`)
- **Mức độ ảnh hưởng:** High (Bảo mật tài khoản & Quản lý phiên - Nguy cơ tấn công chiếm quyền điều khiển phiên Session Hijacking sau khi người dùng chủ động đăng xuất)
- **Tệp kiểm thử tự động tái hiện:** [test_qa_toan_dien.py:test_18](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/tests/test_qa_toan_dien.py#L360)

---

## 2. Tiêu chí kiểm thử & Yêu cầu nghiệp vụ (S1-02)
- **Yêu cầu S1-02:** Người dùng thực hiện đăng xuất khỏi hệ thống. Sau khi đăng xuất, token cũ đã cấp **không được phép tiếp tục sử dụng** để gọi bất kỳ API nào được bảo vệ.
- **Ràng buộc QA nghiêm ngặt:** Không chấp nhận lập luận cho rằng *"hệ thống dùng token stateless / signed token không lưu session nên không cần hủy token phía server"* để đánh giá PASS yêu cầu đăng xuất. Đăng xuất phải có hiệu lực bảo vệ thực tế trên máy chủ.

---

## 3. Các bước tái hiện
1. Đăng nhập tài khoản hợp lệ (ví dụ: `nhanvien1` / `123456`) qua `POST /api/auth/login` và nhận `access_token`.
2. Kiểm tra token hoạt động bình thường bằng cách gọi `GET /api/auth/me` với header `Authorization: Bearer <access_token>` -> Nhận kết quả HTTP 200 OK.
3. Gửi yêu cầu đăng xuất qua `POST /api/auth/logout` với header `Authorization: Bearer <access_token>`.
4. Dùng lại chính `access_token` cũ đó để gửi tiếp yêu cầu đến API bảo vệ `GET /api/auth/me`.

---

## 4. Kết quả mong đợi (Expected Result)
- Bước 3: Endpoint `POST /api/auth/logout` phản hồi thành công (HTTP 200 hoặc HTTP 204).
- Bước 4: Máy chủ từ chối yêu cầu với mã lỗi HTTP 401 Unauthorized kèm thông báo:
  *"Token đã bị thu hồi hoặc phiên làm việc đã kết thúc. Vui lòng đăng nhập lại."*

---

## 5. Kết quả thực tế (Actual Result)
- Tại Bước 3: Endpoint `POST /api/auth/logout` không tồn tại trong backend Flask, trả về mã lỗi **HTTP 404 Not Found**.
- Khi kiểm tra cơ chế xác thực trong `app/auth.py`:
  - Hệ thống sử dụng `itsdangerous.URLSafeTimedSerializer` thuần túy.
  - Hàm `login_required` chỉ giải mã token và kiểm tra `max_age` cùng `is_active` của người dùng.
  - Hoàn toàn **không có bảng lưu token bị thu hồi (Token Blacklist / Revoked Tokens)** hay trường phiên bản xác thực (`credentials_version` / `token_version`) để vô hiệu hóa token cũ khi người dùng đăng xuất.
- Kể cả khi client tự xóa token trên trình duyệt, nếu token đó bị kẻ tấn công đánh cắp trước đó, token vẫn có toàn quyền truy cập hệ thống cho đến khi hết hạn thời gian (mặc định 28.800 giây = 8 tiếng).
- **Bằng chứng kiểm thử tự động:**
  - Test case `test_18_kiem_thu_s1_02_thu_hoi_token_sau_dang_xuat` trong `tests/test_qa_toan_dien.py` ghi nhận trạng thái **FAIL**:
    `AssertionError: 404 not found in (200, 204) : S1-02 CHƯA ĐẠT: Endpoint POST /api/auth/logout không tồn tại hoặc lỗi (HTTP 404). Hệ thống Backend chưa hỗ trợ API đăng xuất!`

---

## 6. Đề xuất khắc phục cho Developer
1. **Phương án 1 (Token Blacklist Table):**
   - Tạo bảng `revoked_tokens (token_jti_or_signature TEXT PRIMARY KEY, revoked_at TIMESTAMP, expires_at TIMESTAMP)`.
   - Viết API `POST /api/auth/logout`: Thêm chữ ký của token hiện tại vào bảng `revoked_tokens`.
   - Tại `app/auth.py` trong decorator `login_required`: Truy vấn bảng `revoked_tokens`, nếu token đã nằm trong danh sách thì từ chối ngay với HTTP 401.
2. **Phương án 2 (Token Version / Credentials Version trên bảng users):**
   - Thêm cột `token_version INTEGER DEFAULT 1` vào bảng `users`.
   - Mã hóa `token_version` vào payload của token: `{"uid": user_id, "tv": token_version}`.
   - Khi gọi `POST /api/auth/logout`, tăng `token_version = token_version + 1` trong bảng `users`.
   - Tại `login_required`, so sánh `payload.get("tv") == user["token_version"]`. Mọi token cấp trước thời điểm đăng xuất sẽ lập tức trở nên vô hiệu.
