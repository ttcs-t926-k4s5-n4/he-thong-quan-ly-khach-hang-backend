# BÁO CÁO KIỂM THỬ BACKEND & ĐIỀU KIỆN ĐƯA LÊN MAIN

- **Người thực hiện:** Đinh Xuân Mạnh (Mã sinh viên: `dtc245200270` - Email: `manhdinh2907@gmail.com`)
- **Vai trò:** Kỹ sư kiểm thử độc lập (Independent QA Engineer)
- **Dự án:** Hệ thống Quản lý Khách hàng (CRM) – Phân hệ Backend API
- **Repository Backend:** `https://github.com/ttcs-t926-k4s5-n4/he-thong-quan-ly-khach-hang-backend.git`
- **Nhánh kiểm thử:** `qa/backend-verification`
- **Thời điểm kiểm thử:** 26/10/2026
- **Môi trường thử nghiệm:** Local Windows, Python 3.14.7, Flask 3.1.3, SQLite 3 (Database độc lập: `instance/crm_test_integration.sqlite3`)
- **Backend Service:** Đang duy trì hoạt động tại `http://127.0.0.1:5000` (API catalog: `http://127.0.0.1:5000/api`)

---

## 1. KẾT LUẬN TỔNG QUAN (VERDICT)

| Hạng mục kiểm tra | Trạng thái | Chi tiết kết quả | Ghi chú |
|---|:---:|:---:|---|
| **Bộ test QA toàn diện mới (`tests/test_qa_toan_dien.py`)** | **FAIL (16 PASS, 2 FAIL)** | 16/18 test PASS; 2 test FAIL tái hiện chính xác lỗi bắt buộc: [BUG-QA-002](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-002-dang-nhap-khoa-5-lan.md) & [BUG-QA-003 / S1-02](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-003-thu-hoi-token-dang-xuat.md). | Tác giả: Đinh Xuân Mạnh (`dtc245200270`). |
| **Bộ kiểm thử phân hệ SCRUM-69/70/71 (`kiem_thu.py`)** | **PASS (21/21)** | 100% tiêu chí chấp nhận đạt, thời gian tải 500 bản ghi đạt 0.0028s (< 1.5s). | Tác giả: PHUC NGUYEN HONG (`dtc245200118`). |
| **Bộ test chung đơn vị kế thừa (`tests/test_scrum*.py`, `test_chung.py`)** | **PASS (76/76)** | 76 test cases nghiệp vụ cốt lõi của các sprint trước đều chạy đạt. | Tác giả: PHUC NGUYEN HONG & Vy Thị Hồng Ngọc. |
| **Lệnh kiểm thử tự động toàn bộ (`chay_kiem_thu.ps1` - unittest discover)** | **FAIL (errors=1)** | `Ran 93 tests ... FAILED (errors=1)`. Module `tests/test_data_scope.py` bị lỗi import thư viện FastAPI TestClient trên nền Flask. | [BUG-QA-001](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/hong-ngoc/BUG-QA-001-test-data-scope.md) do PHUC NGUYEN HONG commit trong `777b0fd`. |
| **Kiểm thử tích hợp Frontend – Backend** | **BLOCKED** | Máy chủ Frontend chưa khởi chạy trong môi trường tích hợp E2E. | Backend đang sẵn sàng tại cổng 5000 cho Frontend kết nối. |
| **ĐIỀU KIỆN ĐƯA LÊN MAIN (MERGE TO MAIN)** | **CHƯA ĐỦ ĐIỀU KIỆN** | **Nghiêm cấm merge vào main lúc này**. Cần giữ mã trên nhánh `qa/backend-verification` cho đến khi Developer khắc phục xong 3 lỗi bắt buộc. | Tuân thủ tuyệt đối quy trình kiểm thử. |

---

## 2. ĐỐI CHIẾU NGUỒN TEST VÀ LỊCH SỬ TÁC GIẢ (ATTRIBUTION)

Để bảo đảm tính minh bạch học thuật và chuẩn hóa trách nhiệm thành viên, toàn bộ các file mã nguồn test và tài liệu trong kho lưu trữ đã được kiểm tra chéo qua `git log`:

1. **PHUC NGUYEN HONG (`dtc245200118@ictu.edu.vn`)**:
   - Tác giả bộ kiểm thử chấp nhận toàn trình `kiem_thu.py` (21 kịch bản kiểm thử khách hàng doanh nghiệp, người liên hệ, trang 360 - commit `072707a`).
   - Tác giả lớp cơ sở `tests/base.py` và bộ test nghiệp vụ Sprint: `test_chung.py` (commit `3b66980`), `test_scrum87_co_hoi.py` (commit `9ecca8c`), `test_scrum88_pipeline.py` (commit `824d886`), `test_scrum89_dong_san_pham.py` (commit `3a7375a`), `test_scrum90_dieu_kien_giai_doan.py` (commit `e616a5d`), `test_scrum99_hoat_dong.py` (commit `eacab85`), `test_scrum100_cong_viec.py` (commit `ba539f6`).
   - Tác giả file dự thảo `tests/test_data_scope.py` (commit `777b0fd` - viết theo kiến trúc FastAPI/SQL Server, gây lỗi `BUG-QA-001`).

2. **Vy Thị Hồng Ngọc (`333807567+dtc245200922-cloud`)**:
   - Tác giả kiểm thử kiểm tra trường bắt buộc khi đăng nhập: `tests/test_qa_hong_ngoc_login.py` (commit `56a84d4`).
   - Tác giả các tài liệu kiểm thử QA ban đầu tại `qa/hong-ngoc/`: `checklist-backend.csv`, `doi-chieu-phan-cong-minh-chung.md`, `tong-hop-kiem-thu.md`, `test-case-dang-nhap.md`, các file `ket-qua-*.txt`, `BUG-QA-001-test-data-scope.md`.

3. **Đinh Xuân Mạnh (`dtc245200270`, email `manhdinh2907@gmail.com`)**:
   - Tác giả bộ kiểm thử QA mở rộng độc lập `tests/test_qa_toan_dien.py` gồm 18 test cases bao phủ bảo mật xác thực, phân quyền dữ liệu (Data Scope), tính toàn vẹn Transaction Rollback, đối chiếu CSDL, cùng 2 test tái hiện lỗi bắt buộc:
     - `test_17_tai_hien_bug_qa_002_khoa_tai_khoan_sau_5_lan_sai`
     - `test_18_kiem_thu_s1_02_thu_hoi_token_sau_dang_xuat`
   - Tác giả các hồ sơ lỗi và báo cáo chuẩn bị merge main trong thư mục riêng:
     - `qa/dinh-xuan-manh/BUG-QA-002-dang-nhap-khoa-5-lan.md`
     - `qa/dinh-xuan-manh/BUG-QA-003-thu-hoi-token-dang-xuat.md`
     - `qa/dinh-xuan-manh/bao-cao-kiem-thu-backend-chuan-bi-main.md`

---

## 3. KẾT QUẢ CHI TIẾT CỦA CÁC BỘ KIỂM THỬ

### 3.1. Bộ test mới độc lập của Đinh Xuân Mạnh (`tests/test_qa_toan_dien.py`)
- **Tổng số test:** 18 test cases.
- **Kết quả:** **16 PASS, 2 FAIL**.
- **Thời gian chạy:** 8.215s.
- **Chi tiết các nhóm test:**
  1. *Đăng nhập, phiên & bảo mật xác thực (test 01 - 08):* PASS 8/8. Đăng nhập đúng cho cả 7 tài khoản thuộc 4 vai trò, từ chối sai mật khẩu, chặn SQL Injection, chặn tài khoản `is_active=0`, từ chối token sai chữ ký, từ chối token hết hạn thời gian.
  2. *Kiểm thử phân quyền dữ liệu Data Scope (test 09 - 11):* PASS 3/3. Nhân viên chỉ xem/sửa cơ hội của mình, trưởng nhóm chỉ xem cơ hội nhóm mình, giám đốc xem toàn bộ. Chặn sửa cơ hội của đồng nghiệp.
  3. *Phân quyền cấu hình & giao việc RBAC (test 12 - 13):* PASS 2/2. Giám đốc có quyền tạo Stage Rules, trưởng nhóm chỉ được override trong nhóm, trưởng nhóm chỉ giao việc cho thành viên thuộc nhóm.
  4. *Toàn vẹn Transaction & Đối chiếu CSDL (test 14 - 16):* PASS 3/3. Khi ghi nhanh hoạt động gặp lỗi công việc -> Transaction rollback 100%, không sinh hoạt động mồ côi. Chặn chuyển giai đoạn không sinh lịch sử sai. Đối chiếu số liệu cơ hội và sản phẩm khớp tuyệt đối với CSDL SQLite.
  5. *Tái hiện lỗi bắt buộc (test 17 & test 18):*
     - `test_17_tai_hien_bug_qa_002_khoa_tai_khoan_sau_5_lan_sai`: **FAIL** (`AssertionError: 200 == 200`). Tái hiện thành công: Backend hiện tại chưa có cơ chế khóa tài khoản 15 phút sau 5 lần sai mật khẩu liên tiếp.
     - `test_18_kiem_thu_s1_02_thu_hoi_token_sau_dang_xuat`: **FAIL** (`AssertionError: 404 not found in (200, 204)`). Tái hiện thành công: Backend thiếu endpoint `POST /api/auth/logout` và token cũ vẫn có thể truy cập API bảo vệ sau khi đăng xuất.

### 3.2. Bộ test chung tự động (`chay_kiem_thu.ps1` / `unittest discover`)
- **Tổng số test nạp được:** 93 tests.
- **Kết quả:** **FAILED (errors=1)**.
- **Nguyên nhân chi tiết:**
  - File `tests/test_data_scope.py` do thành viên PHUC NGUYEN HONG tạo từ sprint trước chứa mã nguồn dành cho framework FastAPI (`from fastapi.testclient import TestClient`, `from app.main import app`, `from app.db import db_cursor`, `SELECT TOP 1`).
  - Dự án thực tế đang sử dụng Flask (`create_app()`, `app/common/`, `app/features/`, `run.py`).
  - Khi cơ chế `unittest discover tests` quét qua file này, tiến trình nạp module bị sập với lỗi `RuntimeError: The starlette.testclient module requires the httpx2 package to be installed.`
  - Kể cả khi có thư viện `httpx`, file này vẫn không thể chạy được trên ứng dụng Flask hiện tại do khác biệt cấu trúc API và cú pháp SQLite.
  - QA không tự ý xóa hay sửa mã test của thành viên khác; đã lập phiếu lỗi `BUG-QA-001` yêu cầu Developer quy hoạch lại module test này.

### 3.3. Bộ test nghiệp vụ khách hàng (`kiem_thu.py`)
- **Kết quả:** **21/21 PASS (100%)**.
- SCRUM-69 (Hồ sơ khách hàng doanh nghiệp): 8/8 PASS.
- SCRUM-70 (Người liên hệ & vai trò mua): 6/6 PASS.
- SCRUM-71 (Trang 360 khách hàng & hiệu năng tải 500 hoạt động): 7/7 PASS (thời gian tải: 0.0028s < 1.5s).

---

## 4. CÁC TIÊU CHÍ NGHIỆP VỤ CHƯA ĐẠT (DEFECT LOG)

### 🔴 BUG-QA-001: Lỗi nạp module kiểm thử `tests/test_data_scope.py`
- **Mức độ:** Blocker / Critical.
- **Mô tả:** Lệnh kiểm thử chung `.\chay_kiem_thu.ps1` không thể chạy hoàn tất (báo lỗi FAILED).
- **Trạng thái:** Chưa sửa (Đã bàn giao Developer).

### 🟡 BUG-QA-002: Sai mật khẩu 5 lần liên tiếp chưa bị khóa tạm thời 15 phút
- **Mức độ:** Medium (Bảo mật tài khoản & Xác thực).
- **Mô tả:** Người dùng nhập sai mật khẩu 5 lần liên tiếp trên `POST /api/auth/login`. Ở lần thứ 6 gửi mật khẩu đúng, hệ thống vẫn cấp token đăng nhập thành công. Bảng `users` thiếu trường lưu số lần sai và thời gian khóa.
- **Tài liệu chi tiết:** [BUG-QA-002-dang-nhap-khoa-5-lan.md](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-002-dang-nhap-khoa-5-lan.md)
- **Tệp test tái hiện:** `tests/test_qa_toan_dien.py:test_17` (ghi nhận FAIL).

### 🔴 BUG-QA-003: Chưa có cơ chế thu hồi token sau khi đăng xuất (Yêu cầu S1-02)
- **Mức độ:** High (Bảo mật phiên làm việc - Chống chiếm đoạt phiên sau đăng xuất).
- **Mô tả:**
  - Hệ thống thiếu API đăng xuất `POST /api/auth/logout` (trả về 404).
  - Backend sử dụng ký token stateless (`URLSafeTimedSerializer`) mà không có danh sách thu hồi (Token Blacklist) hoặc số phiên bản xác thực (`credentials_version`).
  - Sau khi đăng xuất, token cũ vẫn có thể tái sử dụng để truy cập toàn bộ các API được bảo vệ.
- **Tài liệu chi tiết:** [BUG-QA-003-thu-hoi-token-dang-xuat.md](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-003-thu-hoi-token-dang-xuat.md)
- **Tệp test tái hiện:** `tests/test_qa_toan_dien.py:test_18` (ghi nhận FAIL).

---

## 5. THÔNG TIN PHỤC VỤ KIỂM THỬ TÍCH HỢP FRONTEND
- **URL API:** `http://127.0.0.1:5000`
- **Catalog API:** `http://127.0.0.1:5000/api`
- **Cổng Backend:** `5000`
- **Database đang chạy:** `instance/crm_test_integration.sqlite3` (dữ liệu mẫu đã được nạp đầy đủ qua `app.seed`)
- **Tài khoản kiểm thử sẵn có:**
  - `giamdoc` / `123456` (Giám đốc kinh doanh)
  - `truongnhom1` / `123456` (Trưởng nhóm Miền Bắc)
  - `nhanvien1` / `123456` (Nhân viên Miền Bắc)
  - `nhanvien2` / `123456` (Nhân viên Miền Bắc)
  - `truongnhom2` / `123456` (Trưởng nhóm Miền Nam)
  - `nhanvien3` / `123456` (Nhân viên Miền Nam)
  - `quantri` / `123456` (Quản trị hệ thống)

---

## 6. QUYẾT ĐỊNH MERGE VÀO MAIN & HƯỚNG XỬ LÝ TIẾP THEO

1. **Quyết định:** **KHÔNG THỰC HIỆN MERGE VÀO MAIN TẠI THỜI ĐIỂM NÀY.**
2. **Căn cứ quyết định:**
   - Quy định QA: *"Chỉ hợp nhất mã nguồn đã được kiểm thử khi các kiểm tra bắt buộc đạt và không còn lỗi nghiêm trọng. Nếu còn FAIL/BLOCKED ở kiểm tra bắt buộc, giữ trên nhánh QA, báo rõ điều kiện còn thiếu trước khi merge."*
   - Hiện vẫn còn 3 lỗi kiểm thử chưa khắc phục (BUG-QA-001, BUG-QA-002, BUG-QA-003/S1-02).
   - Kiểm thử tích hợp luồng giao diện người dùng (Frontend E2E) đang ở trạng thái BLOCKED.
3. **Các bước tiếp theo:**
   - Lưu trữ toàn bộ kết quả kiểm thử trên nhánh `qa/backend-verification`.
   - Bàn giao danh mục lỗi và kịch bản test cho đội ngũ Developer xử lý.
   - Giữ Backend server chạy liên tục để đội ngũ Frontend tiến hành kiểm thử giao diện và tích hợp.
