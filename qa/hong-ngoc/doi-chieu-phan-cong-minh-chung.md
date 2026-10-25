# ĐỐI CHIẾU PHÂN CÔNG VÀ HỒ SƠ KIỂM THỬ

- Người thực hiện: Vy Thị Hồng Ngọc.
- Vai trò báo cáo: QA.
- Assignee trong bản xuất Jira: Hong Ngoc.
- Dự án: TTCS_T926_K4S5_N4.
- Nguồn phân công: Jira (5).csv.
- Nguồn yêu cầu: Product Backlog của dự án CRM.

## 1. Phạm vi phân công được xác nhận

Bản xuất Jira có 27 issue được giao cho Hong Ngoc,
đều ở trạng thái Done tại thời điểm xuất:

- 24 subtask có tên QA/qa.
- 2 subtask có tên Backend/back.
- 1 task tổng về khóa tài khoản và bàn giao dữ liệu.

Trạng thái Done là trạng thái công việc trên Jira.
Kết quả Pass/Fail phải được đối chiếu riêng với kết quả kiểm thử.

## 2. Danh sách nhiệm vụ QA

| STT | Mã QA | Mã cha | Chức năng | Trạng thái Jira |
|---|---|---|---|---|
| 1 | SCRUM-128 | SCRUM-29 | Phân quyền theo vai trò và dữ liệu sở hữu | Done |
| 2 | SCRUM-140 | SCRUM-30 | Menu điều hướng theo quyền | Done |
| 3 | SCRUM-148 | SCRUM-34 | Khóa tài khoản và bàn giao dữ liệu | Done |
| 4 | SCRUM-165 | SCRUM-64 | Cơ cấu tổ chức kinh doanh | Done |
| 5 | SCRUM-168 | SCRUM-65 | Danh mục dùng chung của bán hàng | Done |
| 6 | SCRUM-171 | SCRUM-66 | Trường tùy chỉnh khách hàng và cơ hội | Done |
| 7 | SCRUM-174 | SCRUM-67 | Cấu hình giai đoạn pipeline và xác suất thắng | Done |
| 8 | SCRUM-177 | SCRUM-68 | Danh mục lý do thắng/thua và đối thủ | Done |
| 9 | SCRUM-192 | SCRUM-73 | Quan hệ công ty mẹ và công ty con | Done |
| 10 | SCRUM-195 | SCRUM-74 | Nhập khách hàng từ Excel | Done |
| 11 | SCRUM-198 | SCRUM-75 | Tìm kiếm và lọc khách hàng | Done |
| 12 | SCRUM-201 | SCRUM-76 | Hỗ trợ sau bán và rủi ro rời bỏ | Done |
| 13 | SCRUM-226 | SCRUM-83 | Quy tắc phân bổ lead tự động | Done |
| 14 | SCRUM-229 | SCRUM-84 | Nhận/từ chối lead và SLA | Done |
| 15 | SCRUM-232 | SCRUM-85 | Chuyển lead thành khách hàng và cơ hội | Done |
| 16 | SCRUM-235 | SCRUM-86 | Danh sách lead, bộ lọc và bộ lọc lưu sẵn | Done |
| 17 | SCRUM-256 | SCRUM-93 | Cảnh báo cơ hội đình trệ | Done |
| 18 | SCRUM-259 | SCRUM-94 | Phân bổ lại cơ hội | Done |
| 19 | SCRUM-262 | SCRUM-95 | Lịch sử thay đổi cơ hội | Done |
| 20 | SCRUM-265 | SCRUM-96 | Tìm kiếm và lọc cơ hội | Done |
| 21 | SCRUM-268 | SCRUM-97 | Chia sẻ cơ hội | Done |
| 22 | SCRUM-283 | SCRUM-102 | Dòng thời gian tương tác khách hàng | Done |
| 23 | SCRUM-286 | SCRUM-103 | Nhắc việc sắp đến hạn và quá hạn | Done |
| 24 | SCRUM-289 | SCRUM-104 | Ghi nhanh kết quả cuộc gọi trên điện thoại | Done |

## 3. Issue khác được giao

| Mã | Tên/loại trên Jira | Nội dung | Trạng thái |
|---|---|---|---|
| SCRUM-34 | Task | Khóa tài khoản và bàn giao dữ liệu; task tổng của SCRUM-147 và SCRUM-148 | Done |
| SCRUM-147 | Backend | Backend khóa tài khoản và bàn giao dữ liệu | Done |
| SCRUM-270 | back | Backend đính kèm tài liệu vào cơ hội; cha SCRUM-98 | Done |

Các issue này được giữ riêng để phản ánh đúng dữ liệu Jira.
Không đổi nhãn Backend/back thành QA.
Chưa có mô tả và minh chứng riêng về phần lập trình trong hồ sơ này.

Không tính SCRUM-34, SCRUM-147 và SCRUM-148
thành ba chức năng khóa tài khoản độc lập.

## 4. Đối chiếu kết quả đã ghi nhận

| Phạm vi | Mã QA được xác nhận | Kết quả hiện có |
|---|---|---|
| Khóa tài khoản và bàn giao | SCRUM-148 | Có kết quả phân tích yêu cầu trong 24–30/09; chưa có số test chạy toàn bộ quy trình |
| Công ty mẹ/con, Excel và lọc khách hàng | SCRUM-192, SCRUM-195, SCRUM-198 | Nằm trong nhóm kiểm thử khách hàng ngày 06/10 và retest 07/10; chưa tách số test theo từng mã |
| Hỗ trợ sau bán/rủi ro | SCRUM-201 | Có nội dung kiểm tra yêu cầu chăm sóc, nhưng chưa mô tả đủ để xác nhận các tiêu chí hỗ trợ sau bán và gắn cờ rủi ro |
| Nhận/từ chối, chuyển đổi, danh sách lead | SCRUM-229, SCRUM-232, SCRUM-235 | Nằm trong đợt phối hợp EP-04 ngày 09/10: 12 trường hợp, 10 đạt, 2 phát sinh lỗi |
| Phân bổ lại cơ hội | SCRUM-259 | Có nội dung kiểm tra chuyển quyền, dữ liệu và lịch sử trong 16–19/10; chưa có số Pass/Fail |
| Lịch sử cơ hội | SCRUM-262 | Có nội dung kiểm tra trước/sau, người và thời điểm trong 16–19/10; chưa có số Pass/Fail |
| Lọc cơ hội | SCRUM-265 | Có nội dung kiểm tra tìm kiếm, tổ hợp điều kiện và lưu bộ lọc trong 16–19/10; chưa có số Pass/Fail |
| Chia sẻ cơ hội | SCRUM-268 | Có nội dung kiểm tra chia sẻ và quyền trong 16–19/10; chưa có số Pass/Fail |

## 5. Nhiệm vụ cần bổ sung kết quả riêng

Những nhiệm vụ dưới đây có trong phân công Jira nhưng phần
kết quả chi tiết hiện có chưa mô tả rõ:

- SCRUM-128: phân quyền vai trò và dữ liệu sở hữu.
- SCRUM-140: menu theo quyền.
- SCRUM-165: cơ cấu tổ chức kinh doanh.
- SCRUM-168: danh mục bán hàng.
- SCRUM-171: trường tùy chỉnh.
- SCRUM-174: cấu hình pipeline và xác suất thắng.
- SCRUM-177: lý do thắng/thua và đối thủ.
- SCRUM-226: phân bổ lead tự động.
- SCRUM-256: cảnh báo cơ hội đình trệ.
- SCRUM-283: timeline khách hàng.
- SCRUM-286: nhắc việc đến hạn/quá hạn.
- SCRUM-289: ghi nhanh cuộc gọi trên điện thoại.

Trạng thái Jira vẫn là Done.
Danh sách này phản ánh phần hồ sơ cần hoàn thiện,
không kết luận người thực hiện chưa làm.

Cần bổ sung kết quả theo từng tiêu chí, ngày chạy,
phiên bản, checklist và ảnh/log phù hợp.
Không tự tạo số Pass/Fail từ trạng thái Done.

## 6. Công việc phối hợp và kiểm thử bổ sung

Các nội dung sau có trong kết quả thực hiện nhưng chưa thấy
issue được giao tương ứng trong bản xuất cá nhân:

- Đăng nhập và khóa tạm sau 5 lần sai.
- Hồ sơ cá nhân S2-02.
- Nhập Excel người dùng S2-01.
- Cảnh báo/gộp khách hàng trùng.
- Danh sách khách hàng cần chăm sóc định kỳ.

Giữ chúng dưới nhóm công việc phối hợp/bổ sung.
Không dùng chúng thay cho các nhiệm vụ QA còn thiếu ở mục 5.

## 7. Kết quả tự động bổ sung

- 66 test_scrum* đạt.
- 7 test_chung đạt.
- 3 test đăng nhập bổ sung đạt.
- Tổng 76 test khác nhau đạt qua các lần chạy riêng.
- 3 trường hợp test_data_scope bị chặn.

Bộ test có thể chỉ bao phủ một phần nhiệm vụ.
Không tự suy ra toàn bộ tiêu chí của 24 nhiệm vụ QA đều đạt.

## 8. Thống kê point theo bản xuất

- 27 issue được giao.
- 16 issue có Story point estimate.
- 11 issue chưa điền point.
- Tổng giá trị đã điền: 55 point.
- Các subtask QA có tổng giá trị đã điền: 52 point.
- SCRUM-270, tên back: 3 point.
- SCRUM-34 và SCRUM-147 chưa điền point.

Không tự điền point còn trống.
Không coi tổng point là tỷ lệ đóng góp hoặc điểm thực tập.

## 9. Tài liệu liên quan

- [Báo cáo kiểm thử](bao-cao-kiem-thu.md).
- [Tổng hợp công việc và kết quả](tong-hop-kiem-thu.md).
- [Test case đăng nhập](test-case-dang-nhap.md).
- Checklist tự động: checklist-backend.csv.

Ngày chuyển Done không thay cho ngày chạy kiểm thử.
Kết quả thiếu minh chứng cần được bổ sung bằng dữ liệu thực tế.
