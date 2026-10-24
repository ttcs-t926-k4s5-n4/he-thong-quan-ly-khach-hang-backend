# ĐỐI CHIẾU NHIỆM VỤ QA VÀ MINH CHỨNG

- Người được phân công: Vy Thị Hồng Ngọc.
- Vai trò: QA.
- Ngày đối chiếu: 25/10/2026.
- Nguồn: Bảng phân công CRM Sprint 1–6 đã tổng hợp phục vụ báo cáo.
- Phạm vi đối chiếu: tài liệu cá nhân trong qa/hong-ngoc.

## 1. Quy ước

- Có log tương ứng: tìm thấy kết quả chạy bộ test liên quan trực tiếp.
- Có bằng chứng một phần: có test liên quan nhưng chưa đủ xác nhận toàn bộ User Story.
- Chưa có minh chứng riêng: chưa nhận diện được kết quả riêng trong thư mục cá nhân; không đồng nghĩa chưa thực hiện công việc.

Trạng thái "Hoàn thành" trong bảng phân công không thay thế kết quả kiểm thử.
Các mục chưa đủ bằng chứng chưa được xác nhận Pass toàn bộ.

## 2. Đối chiếu từng nhiệm vụ

| User Story | Nhiệm vụ được giao | Tình trạng minh chứng | Nội dung cần bổ sung |
|---|---|---|---|
| S1-10 | Khóa tài khoản và bàn giao dữ liệu | Chưa có minh chứng riêng | Khóa tài khoản, chặn đăng nhập, kiểm tra dữ liệu bàn giao |
| S2-06-QA | Cơ cấu tổ chức kinh doanh | Chưa có minh chứng riêng | Tạo/sửa cơ cấu, quan hệ nhóm và phạm vi truy cập |
| S2-07-QA | Danh mục dùng chung của bán hàng | Chưa có minh chứng riêng | Tạo/sửa danh mục, kiểm tra trường bắt buộc và trùng dữ liệu |
| S2-08-QA | Trường tùy chỉnh khách hàng và cơ hội | Chưa có minh chứng riêng | Kiểu dữ liệu, trường bắt buộc, lưu và đọc giá trị |
| S2-09-QA | Cấu hình giai đoạn pipeline và xác suất thắng | Có bằng chứng một phần | Có test xác suất/pipeline; cần kết quả kiểm tra chức năng cấu hình riêng |
| S2-10-QA | Danh mục lý do thắng/thua và đối thủ | Chưa có minh chứng riêng | Quản lý danh mục và sử dụng khi đóng cơ hội |
| S3-05-QA | Quan hệ công ty mẹ và công ty con | Chưa có minh chứng riêng | Liên kết mẹ/con, ngăn vòng lặp và quyền xem |
| S3-06-QA | Nhập khách hàng hàng loạt từ Excel | Chưa có minh chứng riêng | Tệp hợp lệ, sai định dạng, dòng lỗi và dữ liệu trùng |
| S3-07-QA | Tìm kiếm, lọc khách hàng nhiều điều kiện | Có bằng chứng một phần | Có test tra cứu không dấu; cần kiểm tra kết hợp nhiều bộ lọc |
| S3-08-QA | Hỗ trợ sau bán và khách hàng rủi ro rời bỏ | Chưa có minh chứng riêng | Tạo yêu cầu hỗ trợ, gắn cờ và lọc khách hàng rủi ro |
| S4-06-QA | Quy tắc phân bổ lead tự động | Chưa có minh chứng riêng | Cấu hình quy tắc, phân bổ đúng người và trường hợp không khớp |
| S4-07-QA | Nhận/từ chối lead và SLA phản hồi | Chưa có minh chứng riêng | Nhận/từ chối, lý do, quyền thao tác và thời hạn |
| S4-08-QA | Chuyển lead thành khách hàng và cơ hội | Chưa có minh chứng riêng | Điều kiện chuyển đổi, liên kết dữ liệu và ngăn tạo trùng |
| S4-09-QA | Danh sách lead và bộ lọc lưu sẵn | Chưa có minh chứng riêng | Kết hợp bộ lọc, lưu, áp dụng lại và kết quả rỗng |
| S5-05-QA | Đóng cơ hội thắng hoặc thua | Chưa có minh chứng riêng | Quyền đóng, lý do, dữ liệu bắt buộc và lịch sử |
| S5-06-QA | Dự báo doanh số theo trọng số xác suất | Chưa có minh chứng riêng | Đối chiếu công thức, kỳ báo cáo và quyền xem |
| S5-07-QA | Cảnh báo cơ hội đình trệ | Có bằng chứng một phần | Có test cảnh báo trong pipeline; cần kiểm tra đầy đủ phân hệ cảnh báo |
| S5-08-QA | Phân bổ lại cơ hội trong nhóm | Có bằng chứng một phần | Có test giao cơ hội; cần kiểm tra quy trình phân bổ lại và lịch sử |
| S6-06-QA | Tạo và theo dõi công việc có hạn hoàn thành | Có log tương ứng | 7 test của test_scrum100_cong_viec.py đạt; cần đối chiếu thêm tiêu chí chấp nhận |
| S6-07-QA | Lịch làm việc cá nhân và nhóm | Chưa có minh chứng riêng | Lịch cá nhân/nhóm, bộ lọc, trùng lịch và phân quyền |
| S6-08-QA | Dòng thời gian tương tác khách hàng | Có bằng chứng một phần | Có test lịch sử trao đổi; cần kết quả đầy đủ phân hệ timeline |
| S6-09-QA | Nhắc việc sắp đến hạn và quá hạn | Có bằng chứng một phần | Có test quá hạn/nhắc việc; cần kiểm tra đầy đủ phân hệ nhắc việc |
| S6-10-QA | Ghi nhanh kết quả cuộc gọi trên điện thoại | Có bằng chứng một phần | Có test ghi nhanh; cần minh chứng giao diện điện thoại và phân hệ cuộc gọi |

## 3. Tổng hợp

Theo bảng phân công tham chiếu có 23 User Story:
- 1 mục có log bộ test tương ứng.
- 7 mục có bằng chứng liên quan nhưng chưa đủ phạm vi.
- 15 mục chưa có minh chứng riêng được nhận diện.

Đây là thống kê mức độ đầy đủ của hồ sơ minh chứng,
không phải tỷ lệ hoàn thành công việc hoặc tỷ lệ Pass của dự án.

## 4. Đối chiếu mã Jira

Các mã Jira cá nhân đã được cung cấp:
SCRUM-34, SCRUM-147, SCRUM-148, SCRUM-128, SCRUM-140,
SCRUM-165, SCRUM-168, SCRUM-171, SCRUM-226, SCRUM-232,
SCRUM-229, SCRUM-235, SCRUM-174, SCRUM-177, SCRUM-192,
SCRUM-198, SCRUM-195, SCRUM-201.

Chưa có dữ liệu xác minh ánh xạ từng mã Jira với từng User Story.
Cần đối chiếu Key, Summary, Assignee, Status và Parent trên Jira.
Không tự ghép mã theo số thứ tự.

## 5. Mẫu minh chứng cần bổ sung

- Mã Jira/User Story:
- Mã test case:
- Người kiểm thử:
- Ngày kiểm thử:
- Phiên bản code:
- Môi trường:
- Điều kiện và dữ liệu:
- Các bước thực hiện:
- Kết quả mong đợi:
- Kết quả thực tế:
- Trạng thái Pass/Fail/Blocked:
- Đường dẫn ảnh hoặc log:
- Mã lỗi và kết quả kiểm thử lại:

Chỉ điền kết quả thực tế đã quan sát được.
