# Báo cáo kiểm thử backend CRM

Người thực hiện: Vy Thị Hồng Ngọc
Ngày kiểm thử: 22/10/2026
Nhánh: qa/hong-ngoc-backend
Phiên bản code: xem phien-ban-kiem-thu.txt

## Kết quả
- Nhóm test_scrum*: 66 test đạt trong 13.725 giây.
- Nhóm tests.test_chung: 7 test đạt trong 1.911 giây.
- Tổng hai nhóm: 73 test đạt.

## Lỗi còn tồn tại
Lần chạy toàn bộ kết thúc FAILED (errors=1).
Module tests.test_data_scope không nạp được:
ModuleNotFoundError: No module named 'fastapi'.

File test này dùng FastAPI và cú pháp SQL Server.
Backend theo README dùng Flask và SQLite.
Cần Developer xác minh tính tương thích của bộ test.

## Minh chứng
- phien-ban-kiem-thu.txt
- ket-qua-kiem-thu.txt
- ket-qua-test-scrum.txt
- ket-qua-test-chung.txt

## Đóng góp QA
Chạy bộ test có sẵn, đối chiếu kết quả và ghi nhận lỗi.
Không phải tác giả của 73 test.

## Kết luận
73 test thuộc hai nhóm đã đạt.
Chưa kết luận toàn bộ bộ kiểm thử của repo đạt.
