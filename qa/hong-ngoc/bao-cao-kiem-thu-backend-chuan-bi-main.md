# BÁO CÁO KIỂM THỬ BACKEND & ĐIỀU KIỆN ĐƯA LÊN MAIN

- **Người thực hiện:** Đội ngũ QA (Vy Thị Hồng Ngọc & QA Team)
- **Dự án:** Hệ thống Quản lý Khách hàng (CRM) – Backend API Service
- **Repository:** `https://github.com/ttcs-t926-k4s5-n4/he-thong-quan-ly-khach-hang-backend.git`
- **Phiên bản / Commit kiểm thử:** `c75b0c9bdcee133938fe97d3cbdae1a61e397036` (HEAD của `main`, đã chứa commit `ee75b9b` từ `develop` qua PR #37)
- **Thời điểm kiểm thử:** 26/10/2026
- **Môi trường thử nghiệm:** Local Windows 10/11, Python 3.14.7, Flask 3.1.3, SQLite 3 (in-memory & temp isolation)

---

## 1. KẾT LUẬN TỔNG QUAN (VERDICT)

| Hạng mục kiểm tra | Trạng thái | Ghi chú |
|---|:---:|---|
| **Bộ kiểm thử tự động hợp lệ (Valid Suites)** | **PASS (92/92)** | 100% test cases nghiệp vụ hợp lệ đạt (76 test cũ + 16 test QA toàn diện mới). |
| **Kiểm thử tự động phân hệ SCRUM-69/70/71 (`kiem_thu.py`)** | **PASS (21/21)** | 100% tiêu chí chấp nhận đạt, thời gian tải 500 bản ghi đạt 0.0028s (< 1.5s). |
| **Lệnh kiểm thử tự động toàn bộ (`chay_kiem_thu.ps1`)** | **FAIL (errors=1)** | Module `tests/test_data_scope.py` không nạp được do thiếu tương thích thư viện/kiến trúc. |
| **Kiểm thử tích hợp Frontend – Backend** | **BLOCKED** | Máy chủ Frontend chưa được bật (không có tiến trình lắng nghe port 5173/3000). |
| **ĐIỀU KIỆN HỢP NHẤT VÀO MAIN (MERGE TO MAIN)** | **CHƯA ĐỦ ĐIỀU KIỆN** | **Giữ trên nhánh QA**, chờ Developer giải quyết `test_data_scope.py` và phối hợp chạy Frontend. |

---

## 2. HIỆN TRẠNG GIT VÀ XÁC ĐỊNH NHÁNH MÃ NGUỒN

### 2.1. Đối chiếu nhánh `develop` và `main`
- Kiểm tra remote `origin`:
  - `refs/heads/develop`: Commit `ee75b9b` (*Merge PR #36: QA bao cao kiem thu backend*).
  - `refs/heads/main`: Commit `c75b0c9` (*Update test-case-dang-nhap.md*).
- Kết quả đối chiếu (`git merge-base --is-ancestor develop main`):
  - Nhánh `develop` **đã được sáp nhập hoàn toàn vào `main`** qua PR #37 (commit `ef19415 Merge pull request #37 from ttcs-t926-k4s5-n4/develop`).
  - Sau PR #37, nhánh `main` có thêm 10 commits cập nhật tài liệu kiểm thử QA.
  - Nhánh `main` hiện đang phản ánh đầy đủ mã nguồn backend mới nhất.
- Kiểm tra an toàn:
  - Không force push, không `git reset --hard`, bảo toàn toàn bộ commit của các thành viên khác.

---

## 3. KẾT QUẢ KIỂM THỬ BACKEND CHI TIẾT

### 3.1. Chạy các lệnh lint, build và test có sẵn
1. **Kiểm tra cú pháp (Syntax Validation):**
   - Đã quét toàn bộ file Python trong dự án bằng `py_compile`: **100% hợp lệ, không có lỗi cú pháp.**
2. **Chạy `python kiem_thu.py` (SCRUM-69, SCRUM-70, SCRUM-71):**
   - SCRUM-69 (Hồ sơ khách hàng doanh nghiệp): 8/8 tiêu chí ĐẠT (khai báo trường, duy nhất MST, chặn trạng thái sai, phân quyền sở hữu).
   - SCRUM-70 (Người liên hệ & vai trò mua): 6/6 tiêu chí ĐẠT (nhiều liên hệ, 4 vai trò mua, duy nhất 1 đầu mối chính, đổi công ty bảo lưu lịch sử).
   - SCRUM-71 (Trang 360 khách hàng): 7/7 tiêu chí ĐẠT (5 khối thông tin, tính đúng tổng giá trị đã ký và đang mở, hiệu năng tải 500 hoạt động đạt 0.0028s < 1.5s, phân quyền bảo vệ).
3. **Chạy bộ kiểm thử tự động chính thức (`chay_kiem_thu.ps1`):**
   - Kết quả: `Ran 77 tests ... FAILED (errors=1)`.
   - Nguyên nhân: `tests/test_data_scope.py` gặp lỗi `ImportError` / `RuntimeError` khi cố nạp module `fastapi.testclient`.

### 3.2. Kiểm thử Xác thực, Phiên làm việc & Đăng xuất
*(Được tự động hoá và kiểm chứng qua `tests/test_qa_toan_dien.py`)*
- **Đăng nhập hợp lệ:** Kiểm thử thành công trên cả 7 tài khoản đại diện cho 4 cấp bậc: Giám đốc (`giamdoc`), Trưởng nhóm Miền Bắc (`truongnhom1`), Nhân viên Miền Bắc (`nhanvien1`, `nhanvien2`), Trưởng nhóm Miền Nam (`truongnhom2`), Nhân viên Miền Nam (`nhanvien3`), Quản trị viên (`quantri`).
- **Xử lý đăng nhập sai:** Trả về HTTP 401 cùng thông báo chuẩn RESTful tiếng Việt: *"Tên đăng nhập hoặc mật khẩu không đúng."*
- **Chống tấn công SQL Injection:** Các chuỗi injection phổ biến (`' OR '1'='1`, `admin' --`) bị chặn an toàn.
- **Tài khoản bị vô hiệu hoá (`is_active = 0`):**
  - Chặn đăng nhập mới: Trả về HTTP 401 *"Tài khoản đã bị khoá, vui lòng liên hệ quản trị hệ thống."*
  - Hủy phiên tức thì: Khi tài khoản bị khóa trong lúc đang có token hợp lệ, các API nghiệp vụ tiếp theo lập tức từ chối với HTTP 401.
- **Bảo mật Token:**
  - Token bị làm giả / sai chữ ký: Bị từ chối với HTTP 401 *"Token đăng nhập không hợp lệ."*
  - Token quá hạn thời gian (`TOKEN_MAX_AGE_SECONDS`): Bị từ chối với HTTP 401 *"Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."*
- **Cơ chế Đăng xuất:**
  - Hệ thống sử dụng kiến trúc Stateless Bearer Token (URLSafeTimedSerializer). Không có endpoint `POST /api/auth/logout` trên máy chủ (HTTP 404).

### 3.3. Kiểm thử Phân quyền Dữ liệu (Data Scope: Của tôi / Của nhóm / Toàn bộ)
*(Kiểm tra trực tiếp qua API Endpoint)*
1. **Phân hệ Cơ hội bán hàng (`/api/opportunities`):**
   - **Nhân viên (`staff`):** Chỉ thấy và thao tác trên cơ hội mình sở hữu. Khi truy cập trực tiếp ID cơ hội của nhân viên khác qua URL (`GET /api/opportunities/<id>` hoặc `PATCH`), hệ thống trả về HTTP 404 (ẩn tài nguyên để chống rà quét ID).
   - **Trưởng nhóm (`team_lead`):** Thấy và truy cập được toàn bộ cơ hội thuộc nhóm mình quản lý. Khi truy cập ID cơ hội của nhóm khác, hệ thống trả về HTTP 404.
   - **Giám đốc (`director`) & Quản trị (`admin`):** Thấy và thao tác được toàn bộ cơ hội trong công ty.
2. **Cấu hình & Ghi đè Stage Gates (`/api/stage-rules`):**
   - Chỉ Giám đốc được phép tạo/sửa cấu hình điều kiện chuyển giai đoạn. Nhân viên hoặc Trưởng nhóm gọi API cấu hình bị chặn HTTP 403 Forbidden.
   - Trưởng nhóm chỉ được ghi đè (override) điều kiện cho các cơ hội thuộc nhóm mình phụ trách kèm lý do giải trình. Thao tác ghi đè trên cơ hội của nhóm khác bị chặn HTTP 404.
3. **Phân công công việc (`/api/tasks`):**
   - Trưởng nhóm chỉ được giao việc cho thành viên thuộc nhóm mình phụ trách. Cố tình giao việc cho nhân sự nhóm khác bị chặn HTTP 403: *"Trưởng nhóm chỉ được giao việc cho thành viên trong nhóm của mình..."*.
4. **Nhật ký hoạt động (`/api/activities`):**
   - Lịch sử tương tác của khách hàng là dùng chung cho các nhân sự có quyền trên khách hàng, nhưng quyền sửa/xoá hoạt động chỉ thuộc về chính chủ người ghi nhận hoặc Trưởng nhóm trở lên.

### 3.4. Tính toàn vẹn dữ liệu & Transaction Rollback
1. **Ghi nhanh hoạt động kèm công việc tiếp theo (`POST /api/activities/quick`):**
   - Thử nghiệm gửi dữ liệu hoạt động hợp lệ nhưng công việc tiếp theo có hạn hoàn thành ở quá khứ (`due_date < today`).
   - Kết quả: API trả về HTTP 422 lỗi validation.
   - **Đối chiếu Database:** Số lượng bản ghi trong cả 2 bảng `activities` và `tasks` trước và sau thao tác giữ nguyên 100%. Không xuất hiện bản ghi hoạt động mồ côi (Rollback thành công).
2. **Chặn chuyển giai đoạn không sinh dữ liệu rác:**
   - Khi cơ hội chưa đạt điều kiện stage gates, API trả về HTTP 409 Conflict.
   - **Đối chiếu Database:** Trạng thái giai đoạn của cơ hội trong bảng `opportunities` giữ nguyên, bảng `opportunity_stage_history` không bị ghi thêm dòng lịch sử sai lệch.

### 3.5. Đối chiếu phản hồi API với dữ liệu lưu trong Database
- Tạo cơ hội với giá trị khởi điểm 0đ.
- Thêm dòng sản phẩm 1: `DV-TK`, số lượng 2, đơn giá 15.000.000đ, chiết khấu 10% -> Thành tiền: 27.000.000đ.
- Thêm dòng sản phẩm 2: `CRM-STD`, số lượng 10, đơn giá 250.000đ, thuê bao 12 kỳ -> Thành tiền: 30.000.000đ.
- **Đối chiếu trực tiếp SQLite:**
  - Bảng `opportunities`: `amount = 57.000.000đ`, `amount_source = 'lines'`, `estimated_value = 0đ` (giá trị dự kiến thủ công ban đầu được bảo toàn).
  - Bảng `opportunity_lines`: Lưu chuẩn xác 2 dòng với `line_total` lần lượt là 27.000.000đ và 30.000.000đ.

---

## 4. DANH MỤC LỖI & VẤN ĐỀ GHI NHẬN (BUG LOG)

### 🔴 BUG-QA-001: Không nạp được module kiểm thử `tests/test_data_scope.py`
- **Mức độ ảnh hưởng:** Critical (Chặn việc chạy thành công toàn bộ test suite của repo).
- **Hiện trạng:**
  - Lệnh `chay_kiem_thu.ps1` gọi `python -m unittest discover` bị dừng với lỗi `FAILED (errors=1)`.
  - File `test_data_scope.py` nhập các thư viện `fastapi.testclient`, gọi `from app.main import app` và `from app.db import db_cursor`, đồng thời truy vấn câu lệnh SQL dạng `SELECT TOP 1`.
  - Trong khi đó, Backend chuẩn của repo chạy trên Flask, SQLite (cú pháp `LIMIT 1`), module `app.db` không có hàm `db_cursor`.
- **Hành động của QA:**
  - Tuân thủ quy định: **QA không tự ý sửa đổi mã nguồn nghiệp vụ hoặc xóa bỏ test có sẵn để làm test PASS giả tạo**.
  - Đã giữ nguyên file test lỗi để Developer xác minh kiến trúc và chuẩn hóa.
  - Đã xây dựng bộ test chuẩn `tests/test_qa_toan_dien.py` (16 test cases) bao phủ toàn bộ phạm vi data scope trên nền tảng Flask/SQLite hiện tại.

### 🟡 BUG-QA-002: Chưa khóa tạm thời tài khoản sau 5 lần đăng nhập sai liên tiếp
- **Mức độ ảnh hưởng:** Medium (Tiêu chuẩn an toàn thông tin - Chống brute-force dò mật khẩu).
- **Hiện trạng:**
  - Nhập sai mật khẩu 5 lần liên tiếp trên `POST /api/auth/login`, lần thứ 6 nhập đúng thì hệ thống vẫn cấp token thành công ngay.
  - CSDL bảng `users` thiếu cột lưu số lần thử sai và thời gian khóa tạm thời.
- **Hành động của QA:**
  - Đã lập báo cáo chi tiết: `qa/hong-ngoc/BUG-QA-002-dang-nhap-khoa-5-lan.md`.

---

## 5. PHẠM VI CHƯA KIỂM THỬ & ĐIỀU KIỆN BỊ NGHẼN (BLOCKED)

1. **Kiểm thử tích hợp Frontend – Backend:**
   - **Trạng thái:** **BLOCKED**.
   - **Nguyên nhân:** Máy chủ giao diện người dùng (Frontend) chưa được khởi chạy trong môi trường kiểm thử (không có port 5173 / 3000 nào hoạt động).
   - **Ràng buộc QA:** Không kết luận toàn bộ hệ thống PASS khi mới chỉ kiểm thử riêng tầng Backend.
2. **Kiểm thử chịu tải / Stress test nhập file Excel dung lượng lớn:**
   - Hiện mới chỉ kiểm thử unit test chức năng đọc file Excel người dùng/khách hàng ở quy mô dữ liệu mẫu (< 100 dòng). Chưa kiểm thử với file trên 10.000 dòng.

---

## 6. QUYẾT ĐỊNH ĐƯA LÊN MAIN & KHUYẾN NGHỊ

Căn cứ theo quy định QA:
> *"Chỉ hợp nhất mã nguồn đã được kiểm thử khi các kiểm tra bắt buộc đạt và không còn lỗi nghiêm trọng. Nếu còn FAIL/BLOCKED ở kiểm tra bắt buộc, giữ trên nhánh QA, báo rõ điều kiện còn thiếu trước khi merge."*

### Khuyến nghị xử lý:
1. **Lưu giữ thay đổi trên nhánh QA:**
   - Nhánh QA: `qa/backend-verification`.
   - Lưu trữ bộ test mới `tests/test_qa_toan_dien.py`, các phiếu lỗi và báo cáo kiểm thử này.
2. **Điều kiện tiên quyết trước khi mở Pull Request vào `main`:**
   - **Developer cần xử lý BUG-QA-001:** Xác định chuyển đổi `tests/test_data_scope.py` sang tương thích với Flask / SQLite hoặc cấu hình lại nếu là module của dịch vụ khác. Đảm bảo `.\chay_kiem_thu.ps1` chạy ra kết quả `OK` không còn error.
   - **Developer cần xử lý BUG-QA-002:** Bổ sung cơ chế khóa tài khoản 15 phút sau 5 lần sai mật khẩu liên tiếp.
   - **Khởi chạy Frontend:** Tiến hành kiểm thử E2E tích hợp luồng thao tác từ giao diện xuống Backend API trước khi nghiệm thu toàn diện hệ thống.
