#!/usr/bin/env bash
# Tạo 3 nhánh feature/SCRUM-xx-...-backend từ nhánh develop, mỗi nhánh = phần lõi + đúng 1 story.
# Cách dùng (đứng trong thư mục crm-lead-marketing đã chép vào repo):
#   bash scripts/tao-nhanh-feature.sh            # tạo nhánh + commit
#   bash scripts/tao-nhanh-feature.sh --push     # tạo nhánh + commit + push lên origin
#   BASE=main bash scripts/tao-nhanh-feature.sh  # đổi nhánh gốc (mặc định develop)
set -euo pipefail

PUSH=0; [[ "${1:-}" == "--push" ]] && PUSH=1
BASE="${BASE:-develop}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PKG"
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "Thư mục này chưa nằm trong một Git repo."; exit 1; }

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "Có thay đổi chưa commit trong repo. Hãy commit hoặc stash trước khi chạy."; exit 1
fi
git rev-parse --verify --quiet "$BASE" >/dev/null || { echo "Không tìm thấy nhánh '$BASE'."; exit 1; }

CORE=(
  .gitignore .vscode/extensions.json README.md requests.http docs/lead-mau-hoi-thao.xlsx
  python-backend/requirements.txt python-backend/run.py
  python-backend/app/__init__.py python-backend/app/core.py python-backend/app/features/__init__.py
  python-backend/tests/__init__.py python-backend/tests/base.py
  nodejs-backend/package.json nodejs-backend/src/app.js nodejs-backend/src/server.js
  nodejs-backend/src/core/constants.js nodejs-backend/src/core/db.js nodejs-backend/src/core/http.js
  nodejs-backend/src/core/leads.js nodejs-backend/src/core/rateLimiter.js nodejs-backend/src/core/utils.js
  nodejs-backend/src/core/xlsx.js nodejs-backend/test/helpers.js
)
BRANCHES=(
  "feature/SCRUM-78-lead-web-form-backend|scrum78|SCRUM-78|backend thu thập lead từ biểu mẫu nhúng trên website"
  "feature/SCRUM-79-lead-import-excel-backend|scrum79|SCRUM-79|backend tạo lead thủ công và nhập lead hàng loạt từ Excel"
  "feature/SCRUM-80-campaign-tracking-backend|scrum80|SCRUM-80|backend theo dõi lead theo chiến dịch và đo doanh thu"
)
feature_files() {
  case "$1" in
    scrum78) echo "python-backend/app/features/scrum78_web_form.py python-backend/tests/test_scrum78_web_form.py nodejs-backend/src/features/scrum78-web-form.js nodejs-backend/test/scrum78-web-form.test.js";;
    scrum79) echo "python-backend/app/features/scrum79_lead_import.py python-backend/tests/test_scrum79_lead_import.py nodejs-backend/src/features/scrum79-lead-import.js nodejs-backend/test/scrum79-lead-import.test.js";;
    scrum80) echo "python-backend/app/features/scrum80_campaign_tracking.py python-backend/tests/test_scrum80_campaign_tracking.py nodejs-backend/src/features/scrum80-campaign-tracking.js nodejs-backend/test/scrum80-campaign-tracking.test.js";;
  esac
}

# Sao lưu mã nguồn ra thư mục tạm (vì đổi nhánh có thể xoá file khỏi thư mục làm việc)
BACKUP="$(mktemp -d)"
ALL_FILES=("${CORE[@]}" scripts/tao-nhanh-feature.sh scripts/tao-nhanh-feature.ps1)
for b in "${BRANCHES[@]}"; do IFS='|' read -r _ key _ _ <<<"$b"; ALL_FILES+=($(feature_files "$key")); done
tar cf - "${ALL_FILES[@]}" | (cd "$BACKUP" && tar xf -)

for b in "${BRANCHES[@]}"; do
  IFS='|' read -r branch key story msg <<<"$b"
  if git rev-parse --verify --quiet "$branch" >/dev/null; then
    echo ">> Nhánh $branch đã tồn tại — bỏ qua."; continue
  fi
  echo ">> Tạo nhánh $branch từ $BASE"
  git checkout -q "$BASE"
  git checkout -q -b "$branch"
  FILES=("${CORE[@]}" $(feature_files "$key"))
  (cd "$BACKUP" && tar cf - "${FILES[@]}") | tar xf -
  git add -- "${FILES[@]}"
  git commit -q -m "feat($story): $msg (Python + Node.js)" -m "Gồm phần lõi dùng chung, module $story và test tự động theo tiêu chí chấp nhận."
  echo "   Đã commit $(git rev-parse --short HEAD)"
  if [[ $PUSH -eq 1 ]]; then git push -u origin "$branch"; fi
done

git checkout -q "$BASE"
(cd "$BACKUP" && tar cf - .) | tar xf -   # trả lại đầy đủ file vào thư mục làm việc
rm -rf "$BACKUP"
echo "Hoàn tất. Danh sách nhánh:"; git branch --list "feature/SCRUM-7*" "feature/SCRUM-8*"
