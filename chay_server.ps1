# Chạy backend CRM (SCRUM-87, 88, 89, 90, 99, 100) trên Windows PowerShell.
# Cách dùng:
#   .\chay_server.ps1                 Lần đầu: tạo môi trường ảo .venv, cài thư viện, tự tạo dữ liệu mẫu
#   .\chay_server.ps1 -TaoLaiDuLieu   Xoá toàn bộ dữ liệu cũ và tạo lại dữ liệu mẫu trước khi chạy
# Nếu bị chặn chạy script, gõ trước:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
param([switch]$TaoLaiDuLieu)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Không tìm thấy Python. Hãy cài Python 3.10 trở lên và tích chọn 'Add python.exe to PATH'." -ForegroundColor Red
        exit 1
    }
    Write-Host "Đang tạo môi trường ảo .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Host "Không tạo được môi trường ảo." -ForegroundColor Red; exit 1 }
}

Write-Host "Đang kiểm tra / cài thư viện trong requirements.txt ..." -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt --disable-pip-version-check -q
if ($LASTEXITCODE -ne 0) { Write-Host "Cài thư viện thất bại, hãy kiểm tra kết nối mạng." -ForegroundColor Red; exit 1 }

if ($TaoLaiDuLieu) {
    & $venvPython -m app.seed --reset
    if ($LASTEXITCODE -ne 0) { Write-Host "Tạo dữ liệu mẫu thất bại." -ForegroundColor Red; exit 1 }
}

& $venvPython run.py
