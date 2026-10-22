# BUG-QA-001: Không nạp được module kiểm thử test_data_scope

## Người ghi nhận
Vy Thị Hồng Ngọc — QA

## Phạm vi
Chạy bộ kiểm thử backend trên nhánh qa/hong-ngoc-backend.
Phiên bản được kiểm thử: xem phien-ban-kiem-thu.txt.

## Điều kiện
- Đã cài thư viện theo requirements.txt.
- Có môi trường Python .venv của dự án.

## Các bước tái hiện
1. Mở terminal tại thư mục gốc dự án.
2. Chạy lệnh:
   .venv\Scripts\python.exe -m unittest discover -s tests -t . -v
3. Quan sát kết quả nạp module tests.test_data_scope.

## Kết quả mong đợi
Bộ kiểm thử được nạp đầy đủ và chạy được trong môi trường
đã cài đặt theo hướng dẫn của dự án.

## Kết quả thực tế
Lệnh chạy toàn bộ kết thúc với:
FAILED (errors=1)

Module tests.test_data_scope không nạp được:
ModuleNotFoundError: No module named 'fastapi'

## Kết quả kiểm tra bổ sung
- Nhóm test_scrum*: 66 test đạt.
- Nhóm tests.test_chung: 7 test đạt.
- Chưa kết luận toàn bộ bộ kiểm thử của repo đạt.

## Nhận định cần Developer xác minh
requirements.txt hiện khai báo Flask.
test_data_scope.py sử dụng FastAPI TestClient, openpyxl,
app.main, app.db và câu truy vấn có cú pháp SELECT TOP 1.

Có dấu hiệu bộ test này chưa tương thích với backend hiện tại.
Chưa xác nhận nguyên nhân gốc; cài thêm fastapi chưa đủ
để khẳng định lỗi được giải quyết.

## Ảnh hưởng
Chặn việc xác nhận toàn bộ bộ kiểm thử chạy thành công.
Chưa có đủ bằng chứng để kết luận chức năng phân quyền
dữ liệu của ứng dụng bị lỗi.

## Minh chứng
- ket-qua-kiem-thu.txt
- ket-qua-test-scrum.txt
- ket-qua-test-chung.txt
- phien-ban-kiem-thu.txt

## Trạng thái
Đã ghi nhận — chờ Developer xác minh.
Chưa kiểm thử lại sau sửa lỗi.
