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
| **Bộ test chung tự động toàn bộ (`chay_kiem_thu.ps1` - unittest discover)** | **FAILED (failures=2, errors=1)** | `Ran 95 tests ... FAILED (failures=2, errors=1)`. Nạp đủ 18 test mới + 77 test cũ. Exit code = 1. | Kết hợp 1 lỗi nạp module cũ ([BUG-QA-001](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/hong-ngoc/BUG-QA-001-test-data-scope.md)) và 2 test tái hiện lỗi bảo mật. |
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

## 3. KẾT QUẢ ĐỐI SOÁT KIỂM THỬ TỰ ĐỘNG TRÊN COMMIT a5a0b4e

### 3.1. Đối soát lệnh kiểm thử tự động toàn bộ (`chay_kiem_thu.ps1`)
- **Commit thực thi:** `a5a0b4ea88cc1b52dd67699bcbbcc155b4a6a5f2` (nhánh `qa/backend-verification`).
- **Lệnh thực thi:** `powershell -ExecutionPolicy Bypass -File .\chay_kiem_thu.ps1` (gọi lệnh nội bộ: `python -m unittest discover -s tests -t . -v`).
- **Tổng số test được phát hiện và thực thi:** **95 tests**.
- **Kết quả chi tiết:**
  - **Passed:** **92 tests**.
  - **Failures:** **2 tests** (`test_17` và `test_18` trong `tests/test_qa_toan_dien.py`).
  - **Errors:** **1 test** (`tests.test_data_scope` trong `tests/test_data_scope.py`).
  - **Skipped:** **0**.
  - **Thời gian chạy:** 40.024s.
  - **Exit code của script:** **1** (`$LASTEXITCODE = 1`, in ra dòng `"Có kiểm thử chưa đạt, xem chi tiết ở trên."`).
- **Xác nhận nạp bộ test `test_qa_toan_dien.py`:**
  - Bộ test loader đã nạp đầy đủ **18/18 test cases** của `tests/test_qa_toan_dien.py` (từ `test_01` đến `test_18`).
  - 16 test đầu tiên ĐẠT (PASS), 2 test cuối cùng KHÔNG ĐẠT (FAIL) theo đúng thiết kế tái hiện lỗi.
- **Giải thích vì sao báo cáo trước đó chỉ có 1 error:**
  - Ở lần chạy đầu tiên (commit `678e512`), file `tests/test_qa_toan_dien.py` mới chỉ có 16 test cases ban đầu và cả 16 test này đều PASS. Khi đó chỉ có duy nhất lỗi import `test_data_scope.py` (`Ran 93 tests ... FAILED (errors=1)`).
  - Khi bổ sung 2 test tái hiện lỗi (`test_17` và `test_18`) ở commit `a5a0b4e`, tổng số test tăng lên 95 và kết quả tổng hợp của toàn bộ repo hiển thị đầy đủ cả **2 failures** và **1 error**.

### 3.2. Bộ test nghiệp vụ khách hàng (`kiem_thu.py`)
- **Kết quả:** **21/21 PASS (100%)**.
- SCRUM-69 (Hồ sơ khách hàng doanh nghiệp): 8/8 PASS.
- SCRUM-70 (Người liên hệ & vai trò mua): 6/6 PASS.
- SCRUM-71 (Trang 360 khách hàng & hiệu năng tải 500 hoạt động): 7/7 PASS (thời gian tải: 0.0028s < 1.5s).

---

## 4. CÁC TIÊU CHÍ NGHIỆP VỤ CHƯA ĐẠT (DEFECT LOG)

### 🔴 BUG-QA-001: Lỗi nạp module kiểm thử `tests/test_data_scope.py`
- **Mức độ:** Blocker / Critical.
- **Mô tả:** Lệnh kiểm thử chung `.\chay_kiem_thu.ps1` không thể chạy hoàn tất (báo lỗi FAILED errors=1). File import `fastapi.testclient`, `app.main`, `app.db.db_cursor`, câu lệnh `SELECT TOP 1` không tương thích với Flask và SQLite.
- **Trạng thái:** Chưa sửa (Đã bàn giao Developer quy hoạch lại sang chuẩn Flask).

### 🟡 BUG-QA-002: Sai mật khẩu 5 lần liên tiếp chưa bị khóa tạm thời 15 phút
- **Mức độ:** Medium (Bảo mật tài khoản & Xác thực).
- **Mô tả:** Người dùng nhập sai mật khẩu 5 lần liên tiếp trên `POST /api/auth/login`. Ở lần thứ 6 gửi mật khẩu đúng, hệ thống vẫn cấp token đăng nhập thành công (HTTP 200). Không có cơ chế khóa 15 phút sau 5 lần sai.
- **Hồ sơ chi tiết:** [BUG-QA-002-dang-nhap-khoa-5-lan.md](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-002-dang-nhap-khoa-5-lan.md).
- **Tệp test tái hiện:** `tests/test_qa_toan_dien.py:test_17` (ghi nhận FAIL).

### 🔴 BUG-QA-003: Chưa có cơ chế vô hiệu hóa phiên phía máy chủ khi đăng xuất (Yêu cầu S1-02)
- **Mức độ:** High (Bảo mật phiên làm việc - Chống chiếm đoạt phiên sau đăng xuất).
- **Mô tả:**
  - Backend hiện tại chưa có API hoặc luồng đăng xuất (gọi `POST /api/auth/logout` trả về 404). Do đó bước đăng xuất thực tế chưa thể thực hiện được trên máy chủ.
  - Backend sử dụng ký token stateless (`URLSafeTimedSerializer`) mà không có cơ chế vô hiệu hóa phiên phía server (Token Blacklist, Credentials Version...).
  - Sau khi người dùng rời phiên, token cũ vẫn có thể tái sử dụng để truy cập toàn bộ các API được bảo vệ.
- **Hồ sơ chi tiết:** [BUG-QA-003-thu-hoi-token-dang-xuat.md](file:///c:/Users/Dell%20Precision%205550/Downloads/he-thong-quan-ly-khach-hang-backend-main/he-thong-quan-ly-khach-hang-backend-main/qa/dinh-xuan-manh/BUG-QA-003-thu-hoi-token-dang-xuat.md).
- **Tệp test tái hiện:** `tests/test_qa_toan_dien.py:test_18` (ghi nhận FAIL).

---

## 5. THÔNG SỐ BACKEND ĐANG CHẠY PHỤC VỤ FRONTEND
- **URL API:** `http://127.0.0.1:5000`
- **Catalog API:** `http://127.0.0.1:5000/api`
- **Cổng Backend:** `5000`
- **Database đang chạy:** `instance/crm_test_integration.sqlite3`
- **Tài khoản kiểm thử sẵn có:** `giamdoc`, `truongnhom1`, `nhanvien1`, `nhanvien2`, `truongnhom2`, `nhanvien3`, `quantri` (mật khẩu chung: `123456`).
- **Xác minh trực tiếp:** Gọi `GET /api` và `POST /api/auth/login` phản hồi HTTP 200 OK ngay lập tức.

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
   - Retest ngay khi Developer cung cấp bản sửa lỗi, bảo toàn các assertion nghiệp vụ.
   - Tiếp tục duy trì Backend server chạy liên tục để đội ngũ Frontend tiến hành kiểm thử giao diện và tích hợp.
