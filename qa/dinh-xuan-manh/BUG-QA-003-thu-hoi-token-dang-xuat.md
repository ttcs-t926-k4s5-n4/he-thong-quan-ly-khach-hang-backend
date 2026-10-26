# BUG-QA-003: Chưa có cơ chế vô hiệu hóa phiên phía máy chủ khi đăng xuất (Yêu cầu S1-02)

## 1. Thông tin chung
- **Mã lỗi:** BUG-QA-003 (Liên quan yêu cầu nghiệp vụ S1-02)
- **Người phát hiện / Kiểm thử:** Đinh Xuân Mạnh (Mã sinh viên: `dtc245200270` - Email: `manhdinh2907@gmail.com`)
- **Vai trò:** Kỹ sư kiểm thử độc lập (Independent QA Engineer)
- **Ngày ghi nhận:** 26/10/2026
- **Phân hệ / Nghiệp vụ:** Xác thực, Đăng xuất và Quản lý vòng đời phiên làm việc
- **Mức độ ảnh hưởng:** High (An toàn thông tin & Quản trị phiên - Nguy cơ chiếm đoạt phiên sau khi người dùng đã chủ động kết thúc phiên làm việc)
- **Tệp kiểm thử tự động tái hiện:** [test_qa_toan_dien.py:test_18](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/tests/test_qa_toan_dien.py#L360)

---

## 2. Tiêu chí kiểm thử & Yêu cầu nghiệp vụ (S1-02)
- **Yêu cầu cốt lõi S1-02:** Khi người dùng thực hiện đăng xuất / kết thúc phiên, phiên làm việc phải được **vô hiệu hóa ngay lập tức phía server**. Sau thời điểm đó, token đã cấp trước đó không được phép tiếp tục truy cập các API được bảo vệ.
- **Nguyên tắc đánh giá QA:**
  - Đánh giá dựa trên yêu cầu vô hiệu hóa phiên tức thì phía server.
  - Không áp đặt tên endpoint (có thể là `/api/auth/logout`, `/api/sessions/revoke`, hoặc định tuyến khác) hay công nghệ cài đặt nội bộ (Token Blacklist, Token Version, Server session, Redis cache...), miễn là máy chủ có năng lực từ chối token cũ.
  - Không coi việc giải thích "kiến trúc stateless token / signed token tự hết hạn sau TTL" là ĐẠT yêu cầu đăng xuất.

---

## 3. Khảo sát luồng đăng xuất và tài liệu quy định
- **Quy định trong tài liệu thiết kế và các sprint trước:**
  - `sprint1/README.md` (dòng 149): Quy định endpoint `POST /api/auth/logout` - "Đăng xuất".
  - `sprint1/frontend/src/api/index.js` (dòng 32): Frontend gọi hàm `apiLogout = () => post("/auth/logout")`.
  - Prototype `app/main.py` (dòng 189): Thiết kế endpoint `@app.post("/api/auth/logout")` thu hồi phiên với thông báo *"Đã đăng xuất an toàn và thu hồi phiên trên máy chủ."*
- **Khảo sát mã nguồn Backend thực tế hiện tại:**
  - Trong `app/common/routes_auth.py`: Chỉ đăng ký 2 endpoint là `POST /login` và `GET /me`. Hoàn toàn **chưa có bất kỳ endpoint hay luồng xử lý đăng xuất nào được cài đặt**.
  - Trong `app/auth.py`: Hàm `login_required` chỉ kiểm tra tính hợp lệ về mặt thời gian (`TOKEN_MAX_AGE_SECONDS`) và trạng thái `is_active` của user, không có cơ chế kiểm tra tính bị thu hồi của phiên.

---

## 4. Các bước kiểm thử thực tế & Hiện trạng ghi nhận
1. **Bước 1 (Đăng nhập):** Gửi yêu cầu đăng nhập hợp lệ qua `POST /api/auth/login` với tài khoản `nhanvien1` -> Thành công (HTTP 200 OK), nhận `access_token`.
2. **Bước 2 (Xác nhận token hoạt động):** Dùng `access_token` gọi API bảo vệ `GET /api/auth/me` -> Thành công (HTTP 200 OK).
3. **Bước 3 (Thực hiện đăng xuất):**
   - QA gửi yêu cầu đăng xuất tới endpoint quy định theo tài liệu `POST /api/auth/logout`.
   - Kết quả: Máy chủ trả về **HTTP 404 Not Found**.
   - **Ghi nhận trung thực của QA:** Do máy chủ Backend hiện tại **hoàn toàn chưa có luồng đăng xuất**, nên **CHƯA THỂ THỰC HIỆN ĐƯỢC BƯỚC ĐĂNG XUẤT NÀY TRÊN MÁY CHỦ**. QA không mô tả như đã đăng xuất thành công trên server khi API chưa tồn tại.
4. **Bước 4 (Tái sử dụng token cũ):**
   - Dùng chính `access_token` đã cấp ở Bước 1 để gọi lại API được bảo vệ `GET /api/auth/me`.
   - Kết quả: Máy chủ vẫn tiếp nhận và trả về dữ liệu bình thường (HTTP 200 OK). Phiên làm việc vẫn sống nguyên vẹn trên server cho đến khi hết hạn thời gian (8 tiếng).

---

## 5. Kết quả kiểm thử tự động
- Chạy test case `test_18_kiem_thu_s1_02_thu_hoi_token_sau_dang_xuat` trong `tests/test_qa_toan_dien.py`:
  - Trạng thái: **FAIL**.
  - Thông báo lỗi:
    `AssertionError: 404 not found in (200, 204) : S1-02 CHƯA ĐẠT: Endpoint POST /api/auth/logout không tồn tại hoặc lỗi (HTTP 404). Hệ thống Backend chưa hỗ trợ API đăng xuất!`

---

## 6. Đề xuất định hướng cho Developer
Developer có toàn quyền quyết định phương án kỹ thuật và tên endpoint phù hợp:
1. **Bổ sung endpoint đăng xuất:** Tiếp nhận yêu cầu đăng xuất từ client (ví dụ: `POST /api/auth/logout`).
2. **Cơ chế vô hiệu hóa phiên phía server:**
   - *Cách 1 (Token Blacklist):* Lưu trữ chữ ký/jti của token bị hủy vào bảng tạm CSDL hoặc cache cho đến khi hết hạn tự nhiên.
   - *Cách 2 (Phiên bản xác thực - Credentials Version):* Lưu một giá trị `token_version` trên bản ghi người dùng. Khi đăng xuất, tăng giá trị này để lập tức vô hiệu hóa mọi token đã cấp trước đó.
   - *Cách 3 (Session Store):* Quản lý phiên qua bảng phiên đăng nhập tập trung trên server.
