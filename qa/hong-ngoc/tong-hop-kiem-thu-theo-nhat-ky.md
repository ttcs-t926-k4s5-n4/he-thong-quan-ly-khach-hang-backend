# Tổng hợp công việc QA theo nhật ký thực tập

Người thực hiện: Vy Thị Hồng Ngọc — QA.
Nguồn: nội dung nhật ký tuần 3–7 do người thực hiện cung cấp trong lần đối chiếu ngày 25/10/2026.
Đây là bản ghi nhận từ nhật ký, không phải log chạy mới hoặc kết quả đã được xác minh độc lập.
Không tự ánh xạ các mã S1/S2 trong nhật ký sang mã SCRUM khi chưa có dữ liệu Jira.

## 1. Công việc theo tuần được ghi trong nhật ký

| Tuần / khoảng thời gian ghi trong nhật ký | Công việc được ghi nhận | Kết quả theo nhật ký |
|---|---|---|
| Tuần 3: 24–30/09/2026 | Phân tích S1-10: khóa tài khoản khi nhân viên nghỉ việc, thu hồi phiên, bàn giao khách hàng/cơ hội; cập nhật User Story, tiêu chí chấp nhận, ước lượng và ưu tiên trên Jira | Đã làm rõ điều kiện kiểm tra khóa tài khoản, bàn giao và ghi nhật ký; đã cập nhật nhiệm vụ S1-10 trên Jira theo người thực hiện. Chưa có kết quả chạy chức năng cụ thể trong nội dung này |
| Tuần 4: 01–08/10/2026 | Kiểm thử đăng nhập và khóa sau 5 lần sai; S2-02 cập nhật hồ sơ, validation điện thoại, giới hạn sửa email/nhóm/vai trò; phối hợp QA kiểm thử nhập Excel S2-01; tổng hợp lỗi và cập nhật Jira | Ngày 03/10: 3 trường hợp, 2 đạt, 1 chưa đạt. Ngày 04/10: 10 trường hợp hồ sơ, 8 đạt, 2 lỗi. Ghi nhận chưa khóa 15 phút sau 5 lần sai, validation số điện thoại và thông báo vị trí dòng lỗi Excel |
| Tuần 5: 09–15/10/2026 | Kiểm thử khách hàng trùng, công ty mẹ/con, nhập Excel, tìm kiếm/lọc, yêu cầu chăm sóc và danh sách cần chăm sóc; retest; chuẩn bị EP-04, giao diện và phân quyền | Nhật ký dẫn ngày 06/10: 15 trường hợp, 12 đạt, 3 lỗi; 07/10: retest 8 trường hợp, 6 đạt, 2 tồn đọng. Ghi nhận cảnh báo trùng và lọc kết hợp đúng sau sửa; vấn đề giao diện chăm sóc, tốc độ nhập Excel và giao diện EP-04. Các ngày này không nằm trong khoảng tuần ghi ở cột đầu |
| Tuần 6: 16–22/10/2026 | Kiểm thử nhận/từ chối lead, lý do và SLA; chuyển lead thành khách hàng/cơ hội, đối chiếu dữ liệu; danh sách/phân trang/bộ lọc/bộ lọc lưu sẵn; hồi quy và phối hợp Dev | Nhật ký dẫn ngày 09/10: phối hợp 12 trường hợp, 10 đạt, 2 phát sinh lỗi; ghi nhận phản hồi chậm, validation chưa rõ và trạng thái lead sau chuyển đổi chưa đồng bộ bộ lọc lưu sẵn; đã thu thập log gửi Dev theo nhật ký. Ngày 09/10 không thuộc khoảng tuần ở cột đầu |
| Tuần 7: 22–26/10/2026 | Kiểm thử lịch sử giá trị trước/sau, người và thời điểm; tìm kiếm/kết hợp/lưu bộ lọc; chia sẻ cơ hội và quyền; chuyển quyền sở hữu và lịch sử; chuẩn bị/demo báo cáo | Nhật ký ghi đã kiểm thử SCRUM-94, SCRUM-95–96 và SCRUM-97 trong ngày 16–19/10; đối chiếu dữ liệu, quyền và tổ hợp bộ lọc. Chưa có số test Pass/Fail và log riêng kèm theo. Ngày 16–19/10 không thuộc khoảng tuần ở cột đầu |

## 2. Kết quả thủ công do người thực hiện ghi nhận

| Ngày ghi trong nhật ký | Phạm vi | Số trường hợp | Đạt | Chưa đạt/lỗi/tồn đọng theo nhật ký | Minh chứng gốc cần liên kết |
|---|---|---:|---:|---:|---|
| 03/10/2026 | Đăng nhập và khóa tài khoản | 3 | 2 | 1 | Checklist/ảnh/API response và Jira lỗi |
| 04/10/2026 | Hồ sơ cá nhân | 10 | 8 | 2 | Checklist/ảnh validation và quyền sửa |
| 06/10/2026 | Nhóm chức năng khách hàng | 15 | 12 | 3 | Danh sách test case và kết quả từng trường hợp |
| 07/10/2026 | Kiểm thử lại nhóm khách hàng | 8 | 6 | 2 | Phiên bản sửa, liên kết test ban đầu và log retest |
| 09/10/2026 | Phối hợp kiểm thử EP-04 | 12 | 10 | 2 | Test case, phân công phối hợp, log và liên kết Jira |

Không cộng các lượt trên thành số test duy nhất hoặc tỷ lệ Pass chung: có retest, có kiểm thử phối hợp và chưa có danh sách mã test để loại trùng.
Không cộng các số trên với 76 test tự động đã có log.
Không suy ra mỗi số "lỗi" là một bug duy nhất nếu chưa có mã bug.

## 3. Những điểm cần sửa/xác nhận trong nhật ký

1. Các kết quả ngày 06–07/10 đang đặt trong tuần 5 (09–15/10); theo khoảng ngày hiện ghi phải thuộc tuần 4.
2. Kết quả ngày 09/10 đang đặt trong tuần 6 (16–22/10); theo khoảng ngày hiện ghi phải thuộc tuần 5.
3. Kết quả ngày 16–19/10 đang đặt trong tuần 7 (22–26/10); theo khoảng ngày hiện ghi phải thuộc tuần 6.
4. Tuần 6 và tuần 7 cùng có ngày 22/10. Cần xác nhận lịch thực tập để chia khoảng không trùng.
5. Không tự sửa ngày chạy để khớp bảng tuần. Đối chiếu nhật ký ngày/Jira trước khi chuyển dòng.
6. Các hoạt động demo với Mentor và hoàn thành LMS ghi ở phần đào tạo/báo cáo, không tính là test Pass.
7. Những ngày sau 25/10/2026 trong khoảng tổng kết chưa được coi đã hoàn thành chỉ vì có trong kế hoạch.
8. Công việc hồ sơ S2-02, nhập Excel S2-01, gộp trùng/chăm sóc khách hàng, SCRUM-95–97 khác phạm vi chính trong bảng phân công tham chiếu trước đó. Ghi là công việc phối hợp/bổ sung theo nhật ký cho đến khi có Jira xác minh giao nhiệm vụ.

## 4. Phân biệt nguồn bằng chứng

- Nhật ký: có mô tả công việc, ngày và số liệu do người thực hiện ghi nhận.
- Git có log: 76 test tự động khác nhau đạt qua các lần chạy riêng; 3 test data_scope bị chặn.
- File này bổ sung nhật ký vào hồ sơ Git, không có nghĩa các log/ảnh được nhắc trong nhật ký đã được tải lên.
- Kết quả lỗi là lịch sử tại ngày ghi nhận; chưa có retest thì chưa kết luận đã sửa.
- Nguồn log tự động xem [báo cáo kiểm thử](bao-cao-kiem-thu.md); đối chiếu phân công xem [ma trận](doi-chieu-phan-cong-minh-chung.md).

## 5. Hồ sơ cần bổ sung để kiểm chứng

Mỗi lượt kiểm thử cần liên kết: mã Jira/test case, ngày chạy thật, commit/bản chạy, tài khoản mẫu theo vai trò,
bước thực hiện, kết quả mong đợi, kết quả thực tế, log/ảnh và mã lỗi/retest.
Hiện chưa có đủ dữ liệu để xác nhận toàn bộ các chức năng nhật ký đã đạt hoặc các lỗi lịch sử đã khắc phục.

## 6. Học tập và hoạt động nhóm theo nhật ký

- Tuần 3: học/thực hành Web Backend Development với JSP & Servlet; ôn HTML/CSS; nhật ký ghi hoàn thành khóa JSP & Servlet ngày 30/09.
- Tuần 4: Daily meeting, cập nhật Jira, khóa học chuyên môn Frontend/Backend và huấn luyện tăng cường.
- Tuần 5: khóa học chuyên môn, TechTalk 2; nhật ký ghi hoàn thành khóa tự chọn LMS.
- Tuần 6: demo sản phẩm trước Mentor và huấn luyện tăng cường theo nhật ký.
- Tuần 7: nội dung demo, huấn luyện tăng cường và LMS; nhật ký ghi hoàn thành tất cả khóa LMS. Cần đối chiếu trạng thái/ngày hoàn thành trên LMS nếu dùng làm minh chứng.
Các mục này là hoạt động đào tạo/cộng tác, không phải kết quả kiểm thử phần mềm.
