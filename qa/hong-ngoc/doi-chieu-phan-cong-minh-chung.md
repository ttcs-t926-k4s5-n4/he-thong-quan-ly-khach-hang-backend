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

| User Story | Nhiệm vụ theo bảng phân công | Tình trạng log/ảnh riêng | Nội dung cần bổ sung | Đối chiếu nhật ký vừa cung cấp |
|---|---|---|---|---|
| S1-10 | Khóa tài khoản và bàn giao dữ liệu | Chưa có minh chứng riêng | Khóa tài khoản, chặn đăng nhập, kiểm tra dữ liệu bàn giao | Tuần 3: đã phân tích yêu cầu, tiêu chí chấp nhận và cập nhật Jira; nhật ký chưa nêu kết quả chạy bàn giao. |
| S2-06-QA | Cơ cấu tổ chức kinh doanh | Chưa có minh chứng riêng | Tạo/sửa cơ cấu, quan hệ nhóm và phạm vi truy cập | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S2-07-QA | Danh mục dùng chung của bán hàng | Chưa có minh chứng riêng | Tạo/sửa danh mục, kiểm tra trường bắt buộc và trùng dữ liệu | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S2-08-QA | Trường tùy chỉnh khách hàng và cơ hội | Chưa có minh chứng riêng | Kiểu dữ liệu, trường bắt buộc, lưu và đọc giá trị | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S2-09-QA | Cấu hình giai đoạn pipeline và xác suất thắng | Có bằng chứng một phần | Có test xác suất/pipeline; cần kết quả kiểm tra chức năng cấu hình riêng | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S2-10-QA | Danh mục lý do thắng/thua và đối thủ | Chưa có minh chứng riêng | Quản lý danh mục và sử dụng khi đóng cơ hội | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S3-05-QA | Quan hệ công ty mẹ và công ty con | Chưa có minh chứng riêng | Liên kết mẹ/con, ngăn vòng lặp và quyền xem | Nhật ký có công ty mẹ/con trong nhóm khách hàng ngày 06–07/10; chưa tách kết quả riêng. |
| S3-06-QA | Nhập khách hàng hàng loạt từ Excel | Chưa có minh chứng riêng | Tệp hợp lệ, sai định dạng, dòng lỗi và dữ liệu trùng | Nhật ký có nhập Excel khách hàng ngày 06–07/10 và vấn đề tốc độ; chưa có số test riêng. |
| S3-07-QA | Tìm kiếm, lọc khách hàng nhiều điều kiện | Có bằng chứng một phần | Có test tra cứu không dấu; cần kiểm tra kết hợp nhiều bộ lọc | Nhật ký ghi kiểm thử lọc kết hợp và xác nhận đúng sau sửa ngày 07/10; còn thiếu checklist/ảnh gốc. |
| S3-08-QA | Hỗ trợ sau bán và khách hàng rủi ro rời bỏ | Chưa có minh chứng riêng | Tạo yêu cầu hỗ trợ, gắn cờ và lọc khách hàng rủi ro | Nhật ký có yêu cầu chăm sóc và danh sách chăm sóc; chưa xác nhận đồng nhất với hỗ trợ sau bán/rủi ro rời bỏ. |
| S4-06-QA | Quy tắc phân bổ lead tự động | Chưa có minh chứng riêng | Cấu hình quy tắc, phân bổ đúng người và trường hợp không khớp | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S4-07-QA | Nhận/từ chối lead và SLA phản hồi | Chưa có minh chứng riêng | Nhận/từ chối, lý do, quyền thao tác và thời hạn | Nhật ký có nhận/từ chối lead, lý do và SLA; đợt phối hợp ngày 09/10 ghi 12 trường hợp: 10 đạt, 2 lỗi cho cả nhóm EP-04. |
| S4-08-QA | Chuyển lead thành khách hàng và cơ hội | Chưa có minh chứng riêng | Điều kiện chuyển đổi, liên kết dữ liệu và ngăn tạo trùng | Nhật ký có đối chiếu trước/sau chuyển đổi; ghi trạng thái lead chưa đồng bộ bộ lọc lưu sẵn; chưa có số test riêng. |
| S4-09-QA | Danh sách lead và bộ lọc lưu sẵn | Chưa có minh chứng riêng | Kết hợp bộ lọc, lưu, áp dụng lại và kết quả rỗng | Nhật ký có danh sách, phân trang, bộ lọc và bộ lọc lưu sẵn; số liệu nằm chung đợt EP-04 ngày 09/10. |
| S5-05-QA | Đóng cơ hội thắng hoặc thua | Chưa có minh chứng riêng | Quyền đóng, lý do, dữ liệu bắt buộc và lịch sử | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S5-06-QA | Dự báo doanh số theo trọng số xác suất | Chưa có minh chứng riêng | Đối chiếu công thức, kỳ báo cáo và quyền xem | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S5-07-QA | Cảnh báo cơ hội đình trệ | Có bằng chứng một phần | Có test cảnh báo trong pipeline; cần kiểm tra đầy đủ phân hệ cảnh báo | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S5-08-QA | Phân bổ lại cơ hội trong nhóm | Có bằng chứng một phần | Có test giao cơ hội; cần kiểm tra quy trình phân bổ lại và lịch sử | Nhật ký ngày 16–19/10 có SCRUM-94 chuyển quyền sở hữu và lịch sử; chưa có số test riêng. |
| S6-06-QA | Tạo và theo dõi công việc có hạn hoàn thành | Có log tương ứng | 7 test của test_scrum100_cong_viec.py đạt; cần đối chiếu thêm tiêu chí chấp nhận | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S6-07-QA | Lịch làm việc cá nhân và nhóm | Chưa có minh chứng riêng | Lịch cá nhân/nhóm, bộ lọc, trùng lịch và phân quyền | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S6-08-QA | Dòng thời gian tương tác khách hàng | Có bằng chứng một phần | Có test lịch sử trao đổi; cần kết quả đầy đủ phân hệ timeline | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S6-09-QA | Nhắc việc sắp đến hạn và quá hạn | Có bằng chứng một phần | Có test quá hạn/nhắc việc; cần kiểm tra đầy đủ phân hệ nhắc việc | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |
| S6-10-QA | Ghi nhanh kết quả cuộc gọi trên điện thoại | Có bằng chứng một phần | Có test ghi nhanh; cần minh chứng giao diện điện thoại và phân hệ cuộc gọi | Nhật ký chưa nêu rõ mục này; không suy ra chưa làm. Cần đối chiếu phân công/Jira và tài liệu gốc. |

## 3. Thống kê log/ảnh riêng, không phải thống kê việc đã làm

Theo bảng phân công tham chiếu có 23 User Story. Các số dưới đây chỉ xét log/ảnh riêng, KHÔNG bao gồm mô tả nhật ký mới bổ sung:
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

## 6. Cập nhật nguồn nhật ký người thực hiện cung cấp

Đã nhận thêm nhật ký tuần 3–7; xem [tổng hợp nhật ký QA](tong-hop-kiem-thu-theo-nhat-ky.md).
Bảng phía trên là đối chiếu log/tài liệu cá nhân đã có trước khi bổ sung nguồn nhật ký.
"Chưa có minh chứng riêng" trong bảng không có nghĩa không có ghi nhận công việc: nhật ký nay bổ sung các mô tả dưới đây, nhưng chưa có log/ảnh gốc để xác nhận độc lập.

| Phạm vi | Bổ sung từ nhật ký | Giới hạn xác minh |
|---|---|---|
| S1-10 | Phân tích khóa tài khoản, thu hồi phiên, bàn giao và cập nhật Jira tuần 3 | Có ghi nhận phân tích; chưa có log chạy quy trình bàn giao |
| Đăng nhập/khóa sau 5 lần sai | Ngày 03/10 ghi 3 trường hợp: 2 đạt, 1 chưa đạt; lỗi chưa khóa 15 phút | Đây là kết quả thủ công theo nhật ký; khác 3 test login thiếu trường trên Git |
| S2-02 hồ sơ cá nhân | Ngày 04/10 ghi 10 trường hợp: 8 đạt, 2 lỗi | Công việc bổ sung/phối hợp theo nhật ký; cần Jira xác minh phân công và checklist gốc |
| S2-01 nhập Excel người dùng | Phối hợp kiểm thử; ghi lỗi thông báo vị trí dòng | Không đồng nhất với S3-06 nhập Excel khách hàng; chưa có số test riêng |
| Khách hàng: trùng, mẹ/con, Excel, lọc, chăm sóc | Ngày 06/10 ghi 15 trường hợp: 12 đạt, 3 lỗi; ngày 07/10 retest 8: 6 đạt, 2 tồn đọng | Chưa có bảng phân bổ số test theo từng User Story; không gán tất cả kết quả cho một chức năng |
| EP-04 nhận/từ chối lead, SLA, chuyển đổi, danh sách/bộ lọc | Ngày 09/10 phối hợp 12 trường hợp: 10 đạt, 2 lỗi; mô tả trạng thái sau chuyển đổi không đồng bộ bộ lọc lưu sẵn | Chưa có log/ảnh gốc đi kèm; chưa xác nhận mọi lỗi đã sửa |
| SCRUM-94 chuyển quyền sở hữu | Nhật ký ghi kiểm tra dữ liệu, quyền và lịch sử ngày 16–19/10 | Chưa có số test và log riêng |
| SCRUM-95–96 lịch sử, tìm kiếm/lọc cơ hội | Nhật ký ghi đã kiểm thử ngày 16–19/10 | Chưa xác minh ánh xạ S6-01/S6-02 và phân công cá nhân trên Jira |
| SCRUM-97 chia sẻ cơ hội | Nhật ký ghi kiểm tra chia sẻ và quyền ngày 16–19/10 | Chưa có log riêng; chưa xác minh phân công bổ sung trên Jira |

Không xóa các nhiệm vụ đã có trong bảng phân công chỉ vì nhật ký chưa nhắc tới.
Các mục S2-06/07/08/10, S5-05/06 và S6-06/07/08/09/10 cần đối chiếu thêm vì nhật ký vừa cung cấp chưa mô tả rõ từng nhiệm vụ này.
Không đổi tình trạng thiếu log thành Pass chỉ dựa vào mô tả nhật ký.

### Lệch thời gian cần xác nhận
- 06–07/10 không nằm trong tuần 5 ghi 09–15/10.
- 09/10 không nằm trong tuần 6 ghi 16–22/10.
- 16–19/10 không nằm trong tuần 7 ghi 22–26/10.
- 22/10 đang trùng ở tuần 6 và 7.
Giữ nguyên ngày nguồn cho đến khi người thực hiện đối chiếu lịch/Jira.
