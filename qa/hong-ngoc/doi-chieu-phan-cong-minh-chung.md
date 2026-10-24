# Đối chiếu nhiệm vụ QA và minh chứng cá nhân

Người được phân công: Vy Thị Hồng Ngọc.
Ngày đối chiếu: 25/10/2026.
Repo: ttcs-t926-k4s5-n4/he-thong-quan-ly-khach-hang-backend.
Nguồn Git: develop tại ee75b9bf70edc886f60d8421b9cd4f4b747ad42d.

## Nguồn phân công và giới hạn

Nguồn tham chiếu: tài liệu người dùng đã lưu "Bang_phan_cong_CRM_kem_loi_tung_ghi_nhan.docx", mục phân công QA Sprint 1–6.
Đây là bảng tổng hợp phục vụ báo cáo, chưa được xác minh trực tiếp với Jira.
Tài liệu ghi "Hoàn thành" không thay thế log, ảnh hoặc biên bản retest.
Theo bảng tham chiếu: 23 User Story, tổng 20,5 point; không sử dụng số này như tổng Story Point Jira đã xác minh.

Danh sách Jira người dùng đã cung cấp riêng gồm 18 mã:
SCRUM-34, SCRUM-147, SCRUM-148, SCRUM-128, SCRUM-140, SCRUM-165,
SCRUM-168, SCRUM-171, SCRUM-226, SCRUM-232, SCRUM-229, SCRUM-235,
SCRUM-174, SCRUM-177, SCRUM-192, SCRUM-198, SCRUM-195, SCRUM-201.
Chưa có dữ liệu để ánh xạ từng mã Jira sang từng User Story dưới đây. Không suy đoán theo số thứ tự.
Cần bản xuất Jira gồm Key, Summary, Assignee, Status, Parent/User Story và Point để xác minh.

## Ma trận

"Chưa có minh chứng riêng" nghĩa là chưa có kết quả được nhận diện trong bộ tài liệu cá nhân qa/hong-ngoc, không khẳng định chưa làm hoặc chưa có ở mọi nơi.
"Có bằng chứng liên quan" chỉ là bao phủ một phần; chưa được đổi thành Pass toàn bộ User Story.

| User Story | Nội dung được giao | Point tham chiếu | Tình trạng minh chứng cá nhân | Cần kiểm tra/đối chiếu |
|---|---|---:|---|---|
| S1-10 | Khóa tài khoản và bàn giao dữ liệu | 2 | Chưa có minh chứng riêng | Kiểm tra khóa tài khoản, chặn đăng nhập và bàn giao dữ liệu đúng người nhận. |
| S2-06-QA | Cơ cấu tổ chức kinh doanh | 1 | Chưa có minh chứng riêng | Tạo/sửa cơ cấu, quan hệ nhóm và phạm vi truy cập. |
| S2-07-QA | Danh mục dùng chung của bán hàng | 1 | Chưa có minh chứng riêng | Tạo/sửa danh mục, dữ liệu bắt buộc và giá trị trùng. |
| S2-08-QA | Trường tùy chỉnh khách hàng và cơ hội | 0.5 | Chưa có minh chứng riêng | Kiểu dữ liệu, trường bắt buộc và lưu/đọc giá trị. |
| S2-09-QA | Cấu hình giai đoạn pipeline và xác suất thắng | 1 | Có bằng chứng liên quan, chưa đủ phạm vi | Log test_scrum87/test_scrum88 có xác suất và pipeline; chưa xác nhận API cấu hình riêng. |
| S2-10-QA | Danh mục lý do thắng/thua và đối thủ | 1 | Chưa có minh chứng riêng | Quản lý danh mục, ràng buộc nhập liệu và sử dụng khi đóng cơ hội. |
| S3-05-QA | Quan hệ công ty mẹ và công ty con | 0.5 | Chưa có minh chứng riêng | Liên kết mẹ/con, ngăn vòng lặp và quyền xem. |
| S3-06-QA | Nhập khách hàng hàng loạt từ Excel | 0.5 | Chưa có minh chứng riêng | Tệp hợp lệ/sai định dạng, dòng lỗi và dữ liệu trùng. |
| S3-07-QA | Tìm kiếm và lọc khách hàng nhiều điều kiện | 0.5 | Có bằng chứng liên quan, chưa đủ phạm vi | test_chung có tra cứu không phân biệt dấu; chưa chứng minh bộ lọc đa điều kiện/lưu dữ liệu. |
| S3-08-QA | Hỗ trợ sau bán và khách hàng có rủi ro rời bỏ | 1 | Chưa có minh chứng riêng | Tạo yêu cầu hỗ trợ, gắn cờ và lọc khách hàng rủi ro. |
| S4-06-QA | Quy tắc phân bổ lead tự động | 1.5 | Chưa có minh chứng riêng | Cấu hình quy tắc, phân bổ đúng người và xử lý trường hợp không khớp. |
| S4-07-QA | Nhận/từ chối lead và SLA phản hồi | 0.5 | Chưa có minh chứng riêng | Nhận/từ chối, lý do, quyền thao tác và thời hạn phản hồi. |
| S4-08-QA | Chuyển lead thành khách hàng và cơ hội | 0.5 | Chưa có minh chứng riêng | Điều kiện chuyển đổi, dữ liệu liên kết và ngăn tạo trùng. |
| S4-09-QA | Danh sách lead, bộ lọc và bộ lọc lưu sẵn | 0.5 | Chưa có minh chứng riêng | Kết hợp bộ lọc, lưu/áp dụng lại và kết quả rỗng. |
| S5-05-QA | Đóng cơ hội thắng hoặc thua | 1 | Chưa có minh chứng riêng | Quyền đóng, lý do, dữ liệu bắt buộc và lịch sử. |
| S5-06-QA | Dự báo doanh số theo trọng số xác suất | 1 | Chưa có minh chứng riêng | Đối chiếu công thức, kỳ báo cáo và quyền xem. |
| S5-07-QA | Cảnh báo cơ hội đình trệ | 1 | Có bằng chứng liên quan, chưa đủ phạm vi | test_scrum88 có cảnh báo đình trệ; chưa chứng minh đầy đủ phân hệ cảnh báo riêng. |
| S5-08-QA | Phân bổ lại cơ hội trong nhóm | 0.5 | Có bằng chứng liên quan, chưa đủ phạm vi | test_scrum87 có giao cơ hội; chưa chứng minh đầy đủ quy trình phân bổ lại và lịch sử. |
| S6-06-QA | Tạo và theo dõi công việc có hạn hoàn thành | 1 | Có log bộ test tương ứng | 7 test của test_scrum100_cong_viec.py đạt trong ket-qua-test-scrum.txt; kết luận trong phạm vi 7 test. |
| S6-07-QA | Lịch làm việc cá nhân và nhóm | 1 | Chưa có minh chứng riêng | Lịch cá nhân/nhóm, bộ lọc, trùng lịch và phân quyền. |
| S6-08-QA | Dòng thời gian tương tác khách hàng | 1 | Có bằng chứng liên quan, chưa đủ phạm vi | test_scrum99 có lịch sử trao đổi; chưa chứng minh đầy đủ phân hệ timeline khách hàng. |
| S6-09-QA | Nhắc việc sắp đến hạn và quá hạn | 1 | Có bằng chứng liên quan, chưa đủ phạm vi | test_scrum100 có theo dõi quá hạn/nhắc việc; chưa chứng minh đầy đủ phân hệ nhắc việc riêng. |
| S6-10-QA | Ghi nhanh kết quả cuộc gọi trên điện thoại | 1 | Có bằng chứng liên quan, chưa đủ phạm vi | test_scrum99 có ghi nhanh; chưa có minh chứng trình duyệt điện thoại và phân hệ call logging riêng. |

## Tổng hợp khoảng trống

- 1 User Story có log bộ test tương ứng: S6-06-QA; 7 test đạt, không khẳng định bao phủ mọi tiêu chí.
- 7 User Story có bằng chứng liên quan nhưng chưa đủ phạm vi.
- 15 User Story chưa có minh chứng riêng được nhận diện trong bộ tài liệu cá nhân.
- 3 test login QA bổ sung là phần đóng góp thêm, chưa có mã Jira được xác minh.
- Bộ test data_scope có 3 trường hợp bị chặn, không tính Pass.
- Không lấy báo cáo frontend của Đinh Xuân Mạnh làm kết quả thực hiện của Vy Thị Hồng Ngọc.

## Cách bổ sung để kiểm tra được trong báo cáo thực tập

Mỗi User Story cần: mã Jira đã xác minh, phiên bản code, môi trường/ngày chạy,
mã test case, bước thực hiện, kết quả mong đợi, kết quả thực tế, Pass/Fail/Blocked,
link log/ảnh và link bug/retest nếu có.
Chỉ ghi "đã sửa" khi có bằng chứng chạy lại xác nhận.
Không tải dữ liệu khách hàng thật hoặc thông tin đăng nhập riêng vào repo.

Xem [hướng dẫn bổ sung minh chứng](huong-dan-bo-sung-minh-chung.md).
