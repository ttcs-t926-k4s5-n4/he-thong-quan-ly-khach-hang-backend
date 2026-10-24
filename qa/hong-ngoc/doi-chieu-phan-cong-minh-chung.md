# ĐỐI CHIẾU CÔNG VIỆC QA VÀ KẾT QUẢ

Người thực hiện: Vy Thị Hồng Ngọc.
Phạm vi chính của bản tổng hợp: công việc và kết quả tuần 3–7 do người thực hiện cung cấp.
Các mã S1/S2 và SCRUM được giữ đúng nguồn; chưa tự ánh xạ sang 18 mã Jira cá nhân đã liệt kê trước đó.

| Phạm vi công việc | Nội dung thực hiện | Kết quả được ghi nhận | Minh chứng hiện có/cần bổ sung |
|---|---|---|---|
| S1-10 | Phân tích khóa tài khoản khi nghỉ việc, thu hồi phiên, bàn giao khách hàng/cơ hội; tiêu chí chấp nhận, ước lượng, ưu tiên và Jira | Làm rõ điều kiện và cập nhật nhiệm vụ trong 24–30/09 | Có mô tả công việc; cần link Jira; chưa có số test chạy bàn giao |
| Đăng nhập | Thông tin đúng/sai, thông báo và khóa sau 5 lần sai | 03/10: 3 trường hợp, 2 đạt, 1 chưa đạt; chưa khóa 15 phút | Có kết quả tổng hợp; cần test case/ảnh/log và retest |
| S2-02 | Hồ sơ, validation điện thoại, giới hạn sửa email/nhóm/vai trò | 04/10: 10 trường hợp, 8 đạt, 2 lỗi; mô tả lỗi điện thoại | Cần chi tiết riêng cả hai lỗi và minh chứng |
| S2-01 phối hợp | Nhập Excel người dùng | Thông báo vị trí dòng lỗi chưa rõ; chưa có số test riêng | Cần checklist và ảnh; không đồng nhất với Excel khách hàng |
| Nhóm khách hàng | Trùng, mẹ/con, nhập Excel, tìm kiếm/lọc, yêu cầu chăm sóc và danh sách cần chăm sóc | 06/10: 15 trường hợp, 12 đạt, 3 lỗi | Cần phân bổ kết quả theo từng chức năng; không tự gán mã User Story |
| Retest khách hàng | Kiểm tra lại sau sửa | 07/10: 8 trường hợp, 6 đạt, 2 tồn đọng; cảnh báo trùng/lọc kết hợp đúng sau sửa | Cần log retest và nhận diện 2 tồn đọng |
| Chuẩn bị EP-04 | Giao diện, phân quyền ban đầu | Ghi nhận vấn đề giao diện; chưa có số test riêng | Cần ảnh và kết quả quyền riêng |
| EP-04 phối hợp | Nhận/từ chối lead, lý do, SLA, chuyển đổi, dữ liệu trước/sau, danh sách/phân trang/lọc/lưu lọc, hồi quy | 09/10: 12 trường hợp, 10 đạt, 2 lỗi; phản hồi chậm, validation chưa rõ, trạng thái sau chuyển đổi chưa đồng bộ bộ lọc | Có mô tả đã thu thập log gửi Dev; cần tải log/ảnh và link bug; chưa xác nhận mọi lỗi đã sửa |
| SCRUM-94 | Chuyển quyền sở hữu một/nhiều cơ hội, lịch sử và quyền | Đã kiểm tra trong 16–19/10; chưa có số Pass/Fail | Cần kết quả từng trường hợp |
| SCRUM-95–96 | Lịch sử giá trị trước/sau, người/thời điểm, tìm kiếm/kết hợp/lưu lọc | Đã kiểm tra trong 16–19/10; chưa có số Pass/Fail | Cần kết quả từng trường hợp |
| SCRUM-97 | Chia sẻ một/nhiều thành viên, quyền người được chia sẻ | Đã kiểm tra trong 16–19/10; chưa có số Pass/Fail | Cần kết quả từng trường hợp |

## Phần kiểm thử tự động bổ sung

- 73 test có sẵn đã được chạy/đối chiếu; không phải toàn bộ do cá nhân viết.
- 3 test thiếu trường đăng nhập bổ sung có log đạt.
- Tổng 76 test khác nhau đạt qua các lần chạy riêng; 3 trường hợp data_scope bị chặn.
- Những test cơ hội/pipeline/dòng sản phẩm/công việc/hoạt động ngoài phạm vi chính ở bảng trên là kết quả chạy bổ sung/hồi quy, không tự coi là nhiệm vụ được giao hoặc tác giả cá nhân.
- Giữ checklist-backend.csv và log để đối chiếu, không xóa kết quả thực thi có thật nhằm làm khớp hình thức.

## Phân biệt nguồn phân công

Bảng tham chiếu 23 User Story trước đây khác phạm vi công việc cá nhân vừa cung cấp.
Không dùng số 23 hoặc thống kê 1/7/15 cũ làm số nhiệm vụ hoàn thành cho bản tổng hợp này.
Không khẳng định bảng phân công cũ sai; cần Jira để xác nhận chênh lệch.
Các mã SCRUM-34, 147, 148, 128, 140, 165, 168, 171, 226, 232, 229, 235, 174, 177, 192, 198, 195, 201 chưa ánh xạ từng dòng.
Không tự thay đổi Story Point, người phụ trách hoặc trạng thái Jira.

## Hoạt động thực tập

Giữ các nội dung học JSP & Servlet, HTML/CSS, LMS, Daily/Jira, TechTalk 2, huấn luyện tăng cường và demo Mentor trong phần hoạt động thực tập của tong-hop-kiem-thu.md.
Không tính chúng là test case hoặc kết quả Pass.

## Tệp liên quan

- [Tổng hợp đầy đủ](tong-hop-kiem-thu.md)
- [Báo cáo kết quả](bao-cao-kiem-thu.md)
- [Test case đăng nhập](test-case-dang-nhap.md)

Các kết quả thủ công cần log/ảnh gốc để kiểm chứng độc lập. Việc có bản tổng hợp không thay thế bằng chứng thực thi.
