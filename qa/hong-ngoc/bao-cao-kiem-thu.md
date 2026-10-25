# BÁO CÁO KIỂM THỬ HỆ THỐNG QUẢN LÝ KHÁCH HÀNG

- Người thực hiện: Vy Thị Hồng Ngọc.
- Vai trò: QA.
- Dự án: TTCS_T926_K4S5_N4.
- Nguồn phân công: Jira (5).csv.
- Nguồn yêu cầu: Product Backlog CRM.

## 1. Phạm vi trách nhiệm

Theo bản xuất Jira, Hong Ngoc được giao:
- 24 subtask QA, trạng thái Done.
- 2 subtask Backend/back, trạng thái Done.
- 1 task tổng, trạng thái Done.

Báo cáo này tập trung vào công việc QA.
Các issue Backend/back được liệt kê riêng trong
doi-chieu-phan-cong-minh-chung.md.

Phạm vi QA được giao gồm:
- Phân quyền dữ liệu, menu theo quyền, khóa và bàn giao.
- Cơ cấu tổ chức, danh mục bán hàng, trường tùy chỉnh,
  cấu hình pipeline và lý do thắng/thua.
- Công ty mẹ/con, nhập Excel, tìm kiếm/lọc khách hàng,
  hỗ trợ sau bán và rủi ro rời bỏ.
- Phân bổ lead, nhận/từ chối, SLA, chuyển đổi và bộ lọc.
- Cảnh báo đình trệ, phân bổ lại, lịch sử, tìm kiếm/lọc
  và chia sẻ cơ hội.
- Timeline khách hàng, nhắc việc và ghi nhanh cuộc gọi.

Trạng thái Done trên Jira không thay thế kết quả Pass/Fail.

## 2. Công việc có kết quả mô tả

- Phân tích khóa tài khoản, thu hồi phiên và bàn giao dữ liệu.
- Phối hợp kiểm thử đăng nhập, hồ sơ cá nhân và Excel người dùng.
- Kiểm thử nhóm chức năng khách hàng và kiểm thử lại sau sửa.
- Chuẩn bị giao diện và phân quyền ban đầu của EP-04.
- Phối hợp kiểm thử nhận/từ chối lead, SLA, chuyển đổi,
  danh sách, phân trang và bộ lọc.
- Kiểm tra chuyển quyền, lịch sử, tìm kiếm/lọc và chia sẻ cơ hội.
- Chạy bộ test tự động, đối chiếu kết quả và ghi nhận lỗi nạp module.

Các nhiệm vụ được giao nhưng chưa có mô tả kết quả riêng
được giữ trong bảng đối chiếu, không tự ghi đạt.

## 3. Kết quả kiểm thử thủ công

| Ngày | Nội dung | Kết quả ghi nhận |
|---|---|---|
| 24–30/09/2026 | Phân tích khóa và bàn giao S1-10 | Làm rõ điều kiện khóa, thu hồi phiên, bàn giao và ghi lịch sử; cập nhật Jira |
| 03/10/2026 | Đăng nhập và khóa sau 5 lần sai | 3 trường hợp: 2 đạt, 1 chưa đạt |
| 04/10/2026 | Hồ sơ cá nhân | 10 trường hợp: 8 đạt, 2 lỗi |
| Chưa ghi riêng | Phối hợp Excel người dùng | Thông báo vị trí dòng lỗi chưa rõ; chưa có số trường hợp riêng |
| 06/10/2026 | Nhóm khách hàng | 15 trường hợp: 12 đạt, 3 lỗi |
| 07/10/2026 | Kiểm thử lại nhóm khách hàng | 8 trường hợp: 6 đạt, 2 tồn đọng |
| Chưa ghi riêng | Chuẩn bị EP-04 | Ghi nhận vấn đề giao diện; chưa có kết quả quyền riêng |
| 09/10/2026 | Phối hợp EP-04 | 12 trường hợp: 10 đạt, 2 phát sinh lỗi |
| 16–19/10/2026 | Chuyển quyền, lịch sử, lọc và chia sẻ cơ hội | Đã kiểm tra dữ liệu, quyền và tổ hợp bộ lọc; chưa có số Pass/Fail |

Các số liệu thủ công dựa trên kết quả cá nhân được cung cấp.
Chưa có đủ checklist chi tiết, ảnh/log và mã lỗi để xác minh độc lập.

Không cộng các lượt ban đầu, kiểm thử lại và phối hợp
thành số test duy nhất.
Không cộng với số test tự động.

## 4. Vấn đề phát hiện và kết quả kiểm tra lại

| Nhóm | Vấn đề/kết quả | Tình trạng xác nhận |
|---|---|---|
| Đăng nhập | Chưa khóa 15 phút sau 5 lần sai | Chưa có retest xác nhận đã sửa |
| Hồ sơ cá nhân | Validation điện thoại | Chưa có retest riêng |
| Excel người dùng | Thông báo vị trí dòng lỗi chưa rõ | Chưa có retest riêng |
| Khách hàng trùng | Cảnh báo đúng sau sửa ngày 07/10 | Có ghi nhận kết quả retest; cần liên kết minh chứng |
| Lọc khách hàng | Lọc kết hợp đúng sau sửa ngày 07/10 | Có ghi nhận kết quả retest; cần liên kết minh chứng |
| Chăm sóc | Vấn đề giao diện | Chưa có retest riêng |
| Excel khách hàng | Tốc độ nhập chậm | Chưa có số đo và retest riêng |
| EP-04 | Giao diện, phản hồi chậm, validation chưa rõ | Chưa có retest đầy đủ |
| Chuyển đổi lead | Trạng thái chưa đồng bộ với bộ lọc lưu sẵn | Có thông tin thu thập log gửi Dev; chưa xác nhận đã sửa |

Không lấy số dòng trong bảng làm số bug duy nhất.
Chưa xác định cụ thể 2 trường hợp còn tồn đọng ngày 07/10.

## 5. Kết quả kiểm thử tự động bổ sung

| Nhóm | Số test đạt | Minh chứng |
|---|---:|---|
| test_scrum* | 66 | ket-qua-test-scrum.txt |
| tests.test_chung | 7 | ket-qua-test-chung.txt |
| tests.test_qa_hong_ngoc_login | 3 | ket-qua-login-bo-sung.txt |
| Tổng số test khác nhau đạt qua các lần chạy riêng | 76 | Các log nêu trên |

- Log login bổ sung có 10 test: 7 chung và 3 mới.
- Không cộng 7 test chung hai lần.
- Checklist có 79 trường hợp: 76 đạt, 3 bị chặn.
- 3 test thiếu trường đăng nhập khác với 3 trường hợp ngày 03/10.
- Các kết quả không chứng minh toàn bộ 24 nhiệm vụ QA đều đạt.
- Chạy 73 test có sẵn không đồng nghĩa là tác giả của các test đó.

## 6. Lỗi nạp bộ kiểm thử

Log toàn bộ cũ ghi:

Ran 74 tests
FAILED (errors=1)

Module tests.test_data_scope không nạp được:
ModuleNotFoundError: No module named 'fastapi'.

- Đây là log trước khi bổ sung 3 test đăng nhập.
- 3 trường hợp trong module chưa chạy được.
- 1 lỗi import không đồng nghĩa 1 test nghiệp vụ thất bại.
- Chưa đủ bằng chứng kết luận chức năng phân quyền dữ liệu bị lỗi.
- Chờ Developer xác minh tính tương thích của bộ test.
- Chưa có kết quả retest sau sửa.

Chi tiết: BUG-QA-001-test-data-scope.md.

## 7. Đóng góp cá nhân

- Phân tích yêu cầu và đối chiếu tiêu chí chấp nhận.
- Thực hiện/phối hợp kiểm thử các chức năng có ghi nhận.
- Tổng hợp vấn đề, trao đổi với Developer và kiểm thử lại.
- Chạy, đối chiếu 73 test có sẵn.
- Bổ sung 3 test tự động về thiếu trường bắt buộc khi đăng nhập.
- Lập checklist và tổng hợp hồ sơ kiểm thử.

## 8. Hồ sơ cần hoàn thiện

- Kết quả riêng của các nhiệm vụ còn thiếu trong bảng đối chiếu.
- Liên kết Jira, checklist, ảnh/log của các lượt thủ công.
- Mã lỗi và kết quả retest.
- Phiên bản, môi trường và ngày chạy tương ứng.
- Xác nhận lại ngày thực hiện với khoảng tuần.

## 9. Tài liệu liên quan

- [Đối chiếu phân công](doi-chieu-phan-cong-minh-chung.md).
- [Tổng hợp chi tiết](tong-hop-kiem-thu.md).
- [Test case đăng nhập](test-case-dang-nhap.md).
- checklist-backend.csv.
- phien-ban-kiem-thu.txt.

## 10. Kết luận

Phân công cá nhân đã được xác nhận bằng bản xuất Jira.
Kết quả thực hiện được giữ theo từng lượt, không suy diễn từ Done.

76 test tự động khác nhau đạt qua các lần chạy riêng;
3 trường hợp bị chặn.

Chưa xác nhận toàn bộ tiêu chí chức năng đều đạt
hoặc mọi lỗi đã được khắc phục.
