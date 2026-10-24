# BÁO CÁO KIỂM THỬ BACKEND CRM

- Người thực hiện: Vy Thị Hồng Ngọc.
- Vai trò: QA – Kiểm thử phần mềm.
- Dự án: Hệ thống quản lý khách hàng.
- Ngày cập nhật báo cáo: 25/10/2026.
- Phiên bản kiểm thử ban đầu: xem phien-ban-kiem-thu.txt.

## 1. Công việc thực hiện

- Đọc yêu cầu và đối chiếu các chức năng được phân công.
- Chạy các bộ kiểm thử backend có sẵn.
- Tổng hợp checklist, đối chiếu tên test và kết quả thực tế trong log.
- Tài liệu hóa các tình huống đăng nhập và xác thực.
- Bổ sung 3 test tự động kiểm tra đăng nhập khi thiếu trường bắt buộc.
- Ghi nhận lỗi không nạp được bộ kiểm thử phạm vi dữ liệu.
- Rà soát tài liệu và xác định các nhiệm vụ cần bổ sung minh chứng.

## 2. Kết quả kiểm thử đã có minh chứng

| Nhóm kiểm thử | Số test đạt | Minh chứng |
|---|---:|---|
| Các module test_scrum* | 66 | ket-qua-test-scrum.txt |
| Kiểm thử chung tests.test_chung | 7 | ket-qua-test-chung.txt |
| Kiểm thử đăng nhập QA bổ sung | 3 | ket-qua-login-bo-sung.txt |
| Tổng số test khác nhau đạt qua các lần chạy riêng | 76 | Các log nêu trên |

Lưu ý:
- ket-qua-login-bo-sung.txt ghi 10 test đạt, gồm 3 test mới và 7 test_chung.
- Không cộng lại 7 test_chung hai lần.
- 76 test đạt là kết quả tổng hợp qua các lần chạy riêng, không phải kết quả một lần chạy toàn bộ.
- Checklist sau cập nhật có 79 trường hợp: 76 đạt và 3 bị chặn.

## 3. Kiểm thử đăng nhập bổ sung

| Trường hợp | Kết quả mong đợi | Kết quả theo log |
|---|---|---|
| Không gửi tên đăng nhập | HTTP 422; báo thiếu username; không cấp token | Đạt |
| Không gửi mật khẩu | HTTP 422; báo thiếu password; không cấp token | Đạt |
| Gửi JSON rỗng | HTTP 422; báo thiếu cả hai trường; không cấp token | Đạt |

Nguồn mã kiểm thử: tests/test_qa_hong_ngoc_login.py.
Minh chứng: ket-qua-login-bo-sung.txt.

## 4. Lỗi và giới hạn còn tồn tại

Lần chạy toàn bộ trong ket-qua-kiem-thu.txt kết thúc với:

Ran 74 tests
FAILED (errors=1)

Đây là log trước khi bổ sung 3 test đăng nhập mới.

Module tests.test_data_scope không nạp được do:
ModuleNotFoundError: No module named 'fastapi'.

File test sử dụng FastAPI TestClient và cú pháp truy vấn SQL Server,
trong khi bản backend được kiểm tra sử dụng Flask và SQLite.
Cần Developer xác minh tính tương thích của bộ kiểm thử.

Ảnh hưởng:
- 3 trường hợp kiểm thử trong test_data_scope chưa chạy được.
- Chưa đủ bằng chứng kết luận chức năng phân quyền dữ liệu bị lỗi.
- Chưa thể xác nhận toàn bộ bộ kiểm thử của repo đạt.

Chi tiết: BUG-QA-001-test-data-scope.md.
Trạng thái: Chờ Developer xác minh, chưa có kết quả kiểm thử lại sau sửa.

## 5. Đối chiếu nhiệm vụ được giao

Chi tiết xem doi-chieu-phan-cong-minh-chung.md.

Nguồn phân công là bảng tổng hợp phục vụ báo cáo thực tập,
chưa thay thế dữ liệu phân công và trạng thái chính thức trên Jira.

Các nhiệm vụ chưa có minh chứng riêng cần bổ sung:
- Test case và tiêu chí chấp nhận.
- Phiên bản code, môi trường và ngày kiểm thử.
- Kết quả thực tế và trạng thái Pass/Fail/Blocked.
- Log hoặc ảnh minh chứng.
- Liên kết báo lỗi và kết quả kiểm thử lại nếu có.

Không sử dụng trạng thái "Hoàn thành" trong bảng phân công
để tự suy ra chức năng đã kiểm thử đạt.

## 6. Đóng góp cá nhân

- Thực hiện chạy, đối chiếu và tổng hợp kết quả của 73 test có sẵn.
- Bổ sung 3 test tự động về dữ liệu đăng nhập.
- Lập checklist và tài liệu các tình huống xác thực.
- Ghi nhận lỗi nạp bộ kiểm thử phạm vi dữ liệu.
- Tổng hợp khoảng trống minh chứng theo nhiệm vụ được giao.

Không phải tác giả của 73 test có sẵn.
Không tính kết quả thực hiện của thành viên QA khác vào đóng góp cá nhân.

## 7. Kết luận

Theo log đã lưu, 76 test khác nhau đạt qua các lần chạy riêng.
3 trường hợp kiểm thử phạm vi dữ liệu bị chặn.

Chưa kết luận toàn bộ dự án đã đạt yêu cầu kiểm thử.
Cần bổ sung minh chứng cho các nhiệm vụ còn thiếu và chạy lại
bộ kiểm thử trên phiên bản dùng để báo cáo, bàn giao.

## 8. Bổ sung công việc và kết quả theo nhật ký cá nhân

Nguồn mới: nhật ký tuần 3–7 do người thực hiện cung cấp.
Chi tiết: [tong-hop-kiem-thu-theo-nhat-ky.md](tong-hop-kiem-thu-theo-nhat-ky.md).

| Ngày theo nhật ký | Nhóm kiểm thử | Kết quả do người thực hiện ghi nhận |
|---|---|---|
| 03/10/2026 | Đăng nhập và khóa sau 5 lần sai | 3 trường hợp: 2 đạt, 1 chưa đạt |
| 04/10/2026 | Hồ sơ cá nhân | 10 trường hợp: 8 đạt, 2 lỗi |
| 06/10/2026 | Nhóm chức năng khách hàng | 15 trường hợp: 12 đạt, 3 lỗi |
| 07/10/2026 | Kiểm thử lại nhóm khách hàng | 8 trường hợp: 6 đạt, 2 tồn đọng |
| 09/10/2026 | Phối hợp kiểm thử EP-04 | 12 trường hợp: 10 đạt, 2 lỗi |
| 16–19/10/2026 | SCRUM-94, SCRUM-95–96 và SCRUM-97 | Có mô tả kiểm tra dữ liệu, lịch sử, quyền và bộ lọc; chưa có số test |

Các kết quả này là ghi nhận từ nhật ký, chưa có log/ảnh gốc đi kèm trong lần đối chiếu.
Không cộng các lượt thủ công, retest hoặc phối hợp với 76 test tự động.
Các lỗi lịch sử gồm: chưa khóa 15 phút sau 5 lần sai; validation điện thoại; thông báo dòng lỗi Excel;
giao diện/tốc độ nhập; trạng thái lead sau chuyển đổi chưa đồng bộ bộ lọc lưu sẵn.
Chưa có đủ bằng chứng retest để khẳng định tất cả đã sửa.

Nhật ký có ngày lệch khoảng tuần và trùng 22/10; xem tài liệu tổng hợp để xác nhận trước khi nộp.
Lần cập nhật tài liệu này không chạy lại kiểm thử và không thay đổi log gốc.
