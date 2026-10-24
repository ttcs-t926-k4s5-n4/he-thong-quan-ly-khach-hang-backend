# Bổ sung minh chứng kiểm thử phục vụ báo cáo thực tập

## Chạy lại bộ test backend ở thư mục gốc bằng PowerShell

Dùng đúng môi trường .venv của dự án. Ghi phiên bản và ngày chạy vào tệp mới để không thay thế chứng cứ cũ.

```powershell
$qaStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$qaDir = "qa/hong-ngoc/lan-chay-$qaStamp"
New-Item -ItemType Directory -Force $qaDir | Out-Null
git rev-parse HEAD | Set-Content "$qaDir/phien-ban.txt" -Encoding utf8
Get-Date -Format o | Set-Content "$qaDir/thoi-gian.txt" -Encoding utf8
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe --version 2>&1 |
    Out-File "$qaDir/moi-truong.txt" -Encoding utf8
& .\.venv\Scripts\python.exe -m pip freeze 2>&1 |
    Out-File "$qaDir/thu-vien.txt" -Encoding utf8
& .\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v 2>&1 |
    Out-File "$qaDir/ket-qua-toan-bo.txt" -Encoding utf8
$qaExit = $LASTEXITCODE
"ExitCode=$qaExit" | Set-Content "$qaDir/ma-thoat.txt" -Encoding utf8
Get-Content "$qaDir/ket-qua-toan-bo.txt" -Encoding utf8
```

Không đổi FAILED thành OK. Nếu test_data_scope tiếp tục không import được, ghi Blocked và liên kết BUG-QA-001.
Kết quả một phiên bản không tự áp dụng cho phiên bản khác.

## Mẫu ghi nhận kiểm thử thủ công/API

Đây là mẫu trống, không phải kết quả đã thực hiện.

| Trường | Nội dung cần điền |
|---|---|
| Người kiểm thử | Vy Thị Hồng Ngọc |
| Jira / User Story | Key và liên kết đã xác minh |
| Phiên bản / môi trường | Commit, cấu hình chạy và tài khoản mẫu theo vai trò |
| Ngày kiểm thử | Thời gian thực hiện thật |
| Test case | Mã và tiêu chí cần xác minh |
| Dữ liệu / bước thực hiện | Dữ liệu mẫu, request hoặc thao tác cụ thể |
| Mong đợi | Theo tiêu chí chấp nhận đã thống nhất |
| Thực tế | Phản hồi/thao tác quan sát được |
| Kết quả | Pass / Fail / Blocked / Chưa chạy |
| Minh chứng | Đường dẫn log/ảnh trong repo |
| Bug / retest | Liên kết lỗi, phiên bản sửa và kết quả chạy lại |

## Các tài liệu hiện có

- [Báo cáo tổng hợp](bao-cao-kiem-thu.md)
- [Checklist các test tự động](checklist-backend.csv)
- [Test case đăng nhập](test-case-dang-nhap.md)
- [Đối chiếu nhiệm vụ](doi-chieu-phan-cong-minh-chung.md)
- [Lỗi nạp bộ test phạm vi dữ liệu](BUG-QA-001-test-data-scope.md)

Các chức năng được giao nhưng chưa có minh chứng phải bổ sung bằng lần chạy thực tế hoặc tài liệu gốc đã lưu.
