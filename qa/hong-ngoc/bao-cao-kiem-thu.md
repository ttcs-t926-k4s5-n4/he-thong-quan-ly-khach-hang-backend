# Báo cáo kiểm thử backend CRM

Người thực hiện: Vy Thị Hồng Ngọc — QA
Ngày kiểm thử ghi trong báo cáo gốc: 22/10/2026.
Ngày đối chiếu và cập nhật tài liệu: 25/10/2026.
Nhánh nguồn tài liệu đã đối chiếu: develop, commit ee75b9bf70edc886f60d8421b9cd4f4b747ad42d.
Phiên bản lần chạy gốc: xem phien-ban-kiem-thu.txt. Không coi commit đối chiếu tài liệu là phiên bản đã chạy kiểm thử mới.

## Kết quả có minh chứng

| Nhóm | Số test đạt | Minh chứng |
|---|---:|---|
| test_scrum* | 66 | [ket-qua-test-scrum.txt](ket-qua-test-scrum.txt) |
| tests.test_chung | 7 | [ket-qua-test-chung.txt](ket-qua-test-chung.txt) |
| tests.test_qa_hong_ngoc_login | 3 | [ket-qua-login-bo-sung.txt](ket-qua-login-bo-sung.txt) |
| Tổng số test khác nhau đạt qua các lần chạy riêng | 76 | Không phải kết quả một lần chạy toàn bộ |

Log ket-qua-login-bo-sung.txt ghi 10 test đạt, gồm 3 test QA bổ sung và 7 test_chung. Không cộng lại 7 test_chung hai lần.
Checklist sau cập nhật có 79 trường hợp: 76 đạt theo log đã lưu, 3 bị chặn chưa chạy.

## Lần chạy toàn bộ và lỗi còn tồn tại

Log [ket-qua-kiem-thu.txt](ket-qua-kiem-thu.txt) ghi Ran 74 tests, FAILED (errors=1).
Đây là log cũ: 73 test chạy thành công và 1 lỗi nạp module; không phải 74 test nghiệp vụ đã chạy, không bao gồm 3 test login bổ sung.
Trong test_data_scope.py có 3 hàm test chưa chạy được; 1 lỗi import không đồng nghĩa với 1 test nghiệp vụ thất bại.

Module tests.test_data_scope không nạp được: ModuleNotFoundError: No module named 'fastapi'.
File test dùng FastAPI và cú pháp SQL Server; README của bản backend kiểm tra dùng Flask và SQLite.
Xem [BUG-QA-001](BUG-QA-001-test-data-scope.md). Chờ Developer xác minh; chưa có kết quả retest sau sửa.
Giữ nguyên log cũ để bảo toàn bằng chứng, kể cả lỗi hiển thị ký tự tiếng Việt.

## Phạm vi cá nhân và nhiệm vụ được phân công

Xem [ma trận phân công và minh chứng](doi-chieu-phan-cong-minh-chung.md).
23 User Story trong tài liệu phân công tham chiếu không đồng nghĩa 23 chức năng đã kiểm thử đạt.
Các test về cơ hội, pipeline, dòng sản phẩm và hoạt động là kết quả chạy bổ sung/hồi quy; không tự nhận là tác giả hoặc người được giao chính mọi chức năng này.
Các mục chưa có kết quả riêng cần bổ sung bằng chứng thực tế trước khi xác nhận Pass.
Không sử dụng báo cáo của QA khác làm kết quả cá nhân.

## Đóng góp QA

- Chạy và đối chiếu 73 test có sẵn; lập checklist và ghi nhận lỗi nạp bộ test.
- Bổ sung 3 test tự động trong tests/test_qa_hong_ngoc_login.py và lưu log kết quả.
- Tài liệu hóa 4 tình huống từ 2 hàm test có sẵn; 4 tình huống này không tính thêm vào số test tự động.
- Cập nhật ma trận nhiệm vụ, danh sách khoảng trống minh chứng và hướng dẫn chạy lại.

## Kết luận

76 test khác nhau đạt qua các lần chạy riêng theo log đã lưu.
3 trường hợp phạm vi dữ liệu bị chặn. Chưa kết luận toàn bộ bộ kiểm thử hoặc toàn bộ dự án đạt.
Lần cập nhật này chỉ đối chiếu tài liệu, không tạo kết quả chạy mới.
