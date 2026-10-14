# Chạy toàn bộ kiểm thử tự động cho 6 story (mỗi file tests\test_scrumXX_*.py ứng với một story).
# Cách dùng:  .\chay_kiem_thu.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) { $python = $venvPython } else { $python = "python" }

& $python -m unittest discover -s tests -t . -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "Tất cả kiểm thử đều đạt." -ForegroundColor Green
} else {
    Write-Host "Có kiểm thử chưa đạt, xem chi tiết ở trên." -ForegroundColor Red
}
exit $LASTEXITCODE
