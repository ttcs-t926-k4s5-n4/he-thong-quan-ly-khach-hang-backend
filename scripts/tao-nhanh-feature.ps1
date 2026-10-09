# Tạo 3 nhánh feature/SCRUM-xx-...-backend từ nhánh develop, mỗi nhánh = phần lõi + đúng 1 story.
# Cách dùng (đứng trong thư mục crm-lead-marketing đã chép vào repo):
#   powershell -ExecutionPolicy Bypass -File .\scripts\tao-nhanh-feature.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\tao-nhanh-feature.ps1 -Push
#   powershell -ExecutionPolicy Bypass -File .\scripts\tao-nhanh-feature.ps1 -Base main
param([switch]$Push, [string]$Base = "develop")
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Git { & git @args; if ($LASTEXITCODE -ne 0) { throw "Lệnh git thất bại: git $args" } }

$Pkg = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Pkg
& git rev-parse --show-toplevel *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Thư mục này chưa nằm trong một Git repo."; exit 1 }
if (git status --porcelain --untracked-files=no) { Write-Host "Có thay đổi chưa commit. Hãy commit hoặc stash trước."; exit 1 }
& git rev-parse --verify --quiet $Base *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Không tìm thấy nhánh '$Base'."; exit 1 }

$Core = @(
  ".gitignore", ".vscode/extensions.json", "README.md", "requests.http", "docs/lead-mau-hoi-thao.xlsx",
  "python-backend/requirements.txt", "python-backend/run.py",
  "python-backend/app/__init__.py", "python-backend/app/core.py", "python-backend/app/features/__init__.py",
  "python-backend/tests/__init__.py", "python-backend/tests/base.py",
  "nodejs-backend/package.json", "nodejs-backend/src/app.js", "nodejs-backend/src/server.js",
  "nodejs-backend/src/core/constants.js", "nodejs-backend/src/core/db.js", "nodejs-backend/src/core/http.js",
  "nodejs-backend/src/core/leads.js", "nodejs-backend/src/core/rateLimiter.js", "nodejs-backend/src/core/utils.js",
  "nodejs-backend/src/core/xlsx.js", "nodejs-backend/test/helpers.js"
)
$Branches = @(
  @{ Name = "feature/SCRUM-78-lead-web-form-backend"; Story = "SCRUM-78"; Msg = "backend thu thập lead từ biểu mẫu nhúng trên website";
     Files = @("python-backend/app/features/scrum78_web_form.py", "python-backend/tests/test_scrum78_web_form.py",
               "nodejs-backend/src/features/scrum78-web-form.js", "nodejs-backend/test/scrum78-web-form.test.js") },
  @{ Name = "feature/SCRUM-79-lead-import-excel-backend"; Story = "SCRUM-79"; Msg = "backend tạo lead thủ công và nhập lead hàng loạt từ Excel";
     Files = @("python-backend/app/features/scrum79_lead_import.py", "python-backend/tests/test_scrum79_lead_import.py",
               "nodejs-backend/src/features/scrum79-lead-import.js", "nodejs-backend/test/scrum79-lead-import.test.js") },
  @{ Name = "feature/SCRUM-80-campaign-tracking-backend"; Story = "SCRUM-80"; Msg = "backend theo dõi lead theo chiến dịch và đo doanh thu";
     Files = @("python-backend/app/features/scrum80_campaign_tracking.py", "python-backend/tests/test_scrum80_campaign_tracking.py",
               "nodejs-backend/src/features/scrum80-campaign-tracking.js", "nodejs-backend/test/scrum80-campaign-tracking.test.js") }
)

# Sao lưu mã nguồn ra thư mục tạm (vì đổi nhánh có thể xoá file khỏi thư mục làm việc)
$Backup = Join-Path ([System.IO.Path]::GetTempPath()) ("crm-backup-" + [guid]::NewGuid())
function Copy-Files($files, $from, $to) {
  foreach ($f in $files) {
    $dest = Join-Path $to $f
    New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
    Copy-Item -Force (Join-Path $from $f) $dest
  }
}
$All = $Core + @("scripts/tao-nhanh-feature.ps1", "scripts/tao-nhanh-feature.sh")
foreach ($b in $Branches) { $All += $b.Files }
Copy-Files $All $Pkg $Backup

foreach ($b in $Branches) {
  & git rev-parse --verify --quiet $b.Name *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host ">> Nhánh $($b.Name) đã tồn tại — bỏ qua."; continue }
  Write-Host ">> Tạo nhánh $($b.Name) từ $Base"
  Git checkout -q $Base
  Git checkout -q -b $b.Name
  $files = $Core + $b.Files
  Copy-Files $files $Backup $Pkg
  Git add -- @files
  Git commit -q -m "feat($($b.Story)): $($b.Msg) (Python + Node.js)" -m "Gồm phần lõi dùng chung, module $($b.Story) và test tự động theo tiêu chí chấp nhận."
  Write-Host "   Đã commit $(git rev-parse --short HEAD)"
  if ($Push) { Git push -u origin $b.Name }
}

Git checkout -q $Base
Copy-Files $All $Backup $Pkg    # trả lại đầy đủ file vào thư mục làm việc
Remove-Item -Recurse -Force $Backup
Write-Host "Hoàn tất. Danh sách nhánh:"
git branch --list "feature/SCRUM-*"
