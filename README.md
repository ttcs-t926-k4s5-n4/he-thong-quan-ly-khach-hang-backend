# Backend CRM – SCRUM-87, 88, 89, 90, 99, 100

Backend cho 6 story trên Jira:

- **Epic SCRUM-20**: cơ hội bán hàng (SCRUM-87), pipeline kanban (SCRUM-88), sản phẩm/dịch vụ trong cơ hội (SCRUM-89), điều kiện bắt buộc khi rời giai đoạn (SCRUM-90).
- **Epic SCRUM-21**: ghi nhận hoạt động với khách hàng (SCRUM-99), công việc có hạn hoàn thành (SCRUM-100).

Công nghệ: **Python 3.10+, Flask, SQLite** – chỉ cần cài một thư viện là Flask. Mọi thông báo, lỗi kiểm tra dữ liệu và nhãn hiển thị trả về đều bằng tiếng Việt. Có **73 kiểm thử tự động** bám theo từng tiêu chí trên Jira.

## 1. Chạy trên Windows (PowerShell)

```powershell
cd crm_backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # cho phép chạy script trong cửa sổ này
.\chay_server.ps1
```

Lần đầu, script tự tạo môi trường ảo `.venv`, cài Flask và tạo dữ liệu mẫu. Mở trình duyệt tại `http://127.0.0.1:5000/api` để xem danh mục toàn bộ API (kèm mô tả tiếng Việt). Muốn xoá và tạo lại dữ liệu mẫu: `.\chay_server.ps1 -TaoLaiDuLieu`.

Chạy thủ công (không dùng script):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed --reset     # tạo lại dữ liệu mẫu (không bắt buộc, lần đầu chạy server sẽ tự tạo)
python run.py
```

Biến môi trường tuỳ chọn: `CRM_PORT` (mặc định 5000), `CRM_DATABASE` (mặc định `instance\crm.sqlite3`), `CRM_SECRET_KEY` (**bắt buộc đổi khi triển khai thật**), `CRM_TOKEN_MAX_AGE` (giây, mặc định 8 giờ).

## 2. Tài khoản mẫu (mật khẩu chung `123456`)

| Tên đăng nhập | Họ tên | Vai trò | Nhóm |
|---|---|---|---|
| `giamdoc` | Nguyễn Văn An | Giám đốc kinh doanh | – |
| `truongnhom1` | Trần Thị Bình | Trưởng nhóm | Miền Bắc |
| `nhanvien1` | Lê Văn Cường | Nhân viên kinh doanh | Miền Bắc |
| `nhanvien2` | Phạm Thị Dung | Nhân viên kinh doanh | Miền Bắc |
| `truongnhom2` | Hoàng Văn Em | Trưởng nhóm | Miền Nam |
| `nhanvien3` | Vũ Thị Giang | Nhân viên kinh doanh | Miền Nam |
| `quantri` | Quản trị hệ thống | Quản trị hệ thống | – |

Dữ liệu mẫu có sẵn 8 cơ hội ở đủ các giai đoạn (có cơ hội đình trệ, quá ngày chốt, đã thắng, đã thua, một lần trưởng nhóm ghi đè điều kiện), dòng sản phẩm thuê bao, hoạt động, lịch hẹn và công việc (có việc quá hạn, việc đã hoãn, việc trưởng nhóm giao).

## 3. Gọi thử API bằng PowerShell

```powershell
$api = "http://127.0.0.1:5000"
$login = Invoke-RestMethod -Method Post -Uri "$api/api/auth/login" -ContentType "application/json; charset=utf-8" `
         -Body ([Text.Encoding]::UTF8.GetBytes('{"username":"nhanvien1","password":"123456"}'))
$h = @{ Authorization = "Bearer $($login.access_token)" }

# Bảng kanban của tôi (SCRUM-88)
Invoke-RestMethod -Uri "$api/api/pipeline/board" -Headers $h | ConvertTo-Json -Depth 8

# Tạo công việc hạn sau 3 ngày (SCRUM-100) – gửi body dạng byte UTF-8 để giữ dấu tiếng Việt
$body = @{ title = "Gửi báo giá cho khách"; due_date = (Get-Date).AddDays(3).ToString("yyyy-MM-dd"); priority = "high"; customer_id = 1 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$api/api/tasks" -Headers $h -ContentType "application/json; charset=utf-8" `
                  -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

Mọi API (trừ đăng nhập và danh mục `/api`) cần header `Authorization: Bearer <token>`.

## 4. Story → tiêu chí → API → mã nguồn

### SCRUM-87 – Tạo và quản lý cơ hội bán hàng
Mã nguồn: `app/features/opportunities/` · Kiểm thử: `tests/test_scrum87_co_hoi.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Khai báo tên, khách hàng, người liên hệ chính, giai đoạn, giá trị dự kiến, ngày dự kiến chốt, nguồn | `POST /api/opportunities`; người liên hệ phải thuộc đúng khách hàng; không gửi giai đoạn thì mặc định "Tiếp cận" |
| Xác suất thắng mặc định theo giai đoạn, sửa tay được kèm ghi chú | Xác suất khác mặc định bắt buộc có `probability_note`; đặt lại bằng mặc định thì bỏ đánh dấu sửa tay |
| Một khách hàng có nhiều cơ hội song song | Không giới hạn; thông báo cho biết khách đang có bao nhiêu cơ hội mở |
| Ngày dự kiến chốt không ở quá khứ khi tạo mới | Báo lỗi 422 kèm ngày hôm nay |

Các API khác: `GET /api/opportunities` (lọc `customer_id`, `stage_id`, `owner_id`, `status`, `q`, `close_from`, `close_to`), `GET/PATCH/DELETE /api/opportunities/{id}`.

### SCRUM-88 – Bảng pipeline dạng kanban
Mã nguồn: `app/features/pipeline/` · Kiểm thử: `tests/test_scrum88_pipeline.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Mỗi cột là một giai đoạn, có số cơ hội và tổng giá trị | `GET /api/pipeline/board` trả `columns[]` với `count`, `total_amount`, `weighted_amount` |
| Kéo thả để chuyển giai đoạn | `POST /api/pipeline/cards/{id}/move` với `to_stage_id`; trả thẻ mới và số liệu mới của 2 cột; vẫn áp dụng điều kiện SCRUM-90 |
| Thẻ hiển thị tên khách, giá trị, ngày dự kiến chốt, cảnh báo đình trệ | `cards[]` có `customer_name`, `amount`, `expected_close_date`, `is_stale`, `is_overdue`, `warnings[]` |
| Lọc theo người sở hữu, nhóm, khoảng ngày chốt; nhân viên mặc định chỉ thấy của mình | Tham số `owner_id`, `team_id`, `close_from`, `close_to`; phạm vi theo vai trò (SCRUM-29) |

### SCRUM-89 – Sản phẩm/dịch vụ trong cơ hội
Mã nguồn: `app/features/opportunity_lines/` · Kiểm thử: `tests/test_scrum89_dong_san_pham.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Chọn từ danh mục, nhập số lượng và đơn giá; đơn giá mặc định theo bảng giá niêm yết | `GET /api/products`; `POST /api/opportunities/{id}/lines` – không gửi `unit_price` thì lấy giá niêm yết |
| Giá trị cơ hội tự tính lại từ các dòng | Mỗi lần thêm/sửa/xoá dòng đều tính lại; xoá hết dòng thì quay về giá trị dự kiến nhập tay |
| Thuê bao khai báo số kỳ và giá trị hợp đồng theo năm | `periods` (số kỳ) bắt buộc với thuê bao; trả `annual_value`, `term_months`, `yearly_breakdown` |

### SCRUM-90 – Điều kiện bắt buộc khi rời giai đoạn
Mã nguồn: `app/features/stage_gates/` · Kiểm thử: `tests/test_scrum90_dieu_kien_giai_doan.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Không cho chuyển nếu chưa thoả điều kiện đã cấu hình | Giám đốc cấu hình qua `POST /api/stage-rules`; loại điều kiện: số hoạt động đã diễn ra (vd. cuộc gặp), thông tin bắt buộc, số dòng sản phẩm, giá trị tối thiểu |
| Thông báo nêu rõ còn thiếu gì | Lỗi 409 `STAGE_CONDITIONS_UNMET` kèm `missing_conditions[]`; `GET /api/opportunities/{id}/stage-check` kiểm tra trước |
| Trưởng nhóm trở lên ghi đè kèm lý do | Gửi `override: true` và `override_reason` (≥ 10 ký tự); lưu ở `/stage-history`, xem nhật ký tại `/api/stage-rules/overrides` |

### SCRUM-99 – Ghi nhận hoạt động với khách hàng
Mã nguồn: `app/features/activities/` · Kiểm thử: `tests/test_scrum99_hoat_dong.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Loại: cuộc gọi, cuộc gặp, email, ghi chú | `activity_type`: `call`, `meeting`, `email`, `note` |
| Gắn với khách hàng, người liên hệ, cơ hội | Chỉ gửi cơ hội hoặc người liên hệ thì tự suy ra khách hàng; kiểm tra liên kết đúng khách hàng |
| Ghi thời điểm, thời lượng, nội dung, kết quả | `occurred_at`, `duration_minutes`, `content`, `outcome` |
| Ghi được hoạt động trong quá khứ | Thời điểm quá khứ → "Đã diễn ra"; tương lai → "Sắp diễn ra" (chỉ cuộc gọi/cuộc gặp) |
| Dùng nhanh trên điện thoại | `POST /api/activities/quick`, `GET /api/activities/quick-suggestions`, `POST /api/activities/{id}/complete` |

Lịch sử trao đổi dùng chung của một khách hàng: `GET /api/customers/{id}/activities`.

### SCRUM-100 – Công việc có hạn hoàn thành
Mã nguồn: `app/features/tasks/` · Kiểm thử: `tests/test_scrum100_cong_viec.py`

| Tiêu chí | Cách đáp ứng |
|---|---|
| Tiêu đề, hạn, mức ưu tiên, người thực hiện, gắn khách hàng hoặc cơ hội | `POST /api/tasks`; bắt buộc gắn khách hàng hoặc cơ hội; hạn không ở quá khứ |
| Đánh dấu hoàn thành, hoãn kèm lý do | `POST /api/tasks/{id}/complete`, `/postpone` (lý do ≥ 5 ký tự, có lịch sử hoãn), `/reopen` |
| Trưởng nhóm giao việc cho thành viên trong nhóm | `assignee_id` khi tạo hoặc `POST /api/tasks/{id}/assign`; nhân viên chỉ tạo việc cho chính mình |

Theo dõi: `GET /api/tasks` (lọc `due=overdue|today|next_7_days`, `assigned_to_me`...) và `GET /api/tasks/reminders`.

## 5. Quy ước chung

- **Phân quyền dữ liệu** thống nhất với SCRUM-29: nhân viên thấy dữ liệu của mình, trưởng nhóm thấy cả nhóm, giám đốc và quản trị thấy tất cả. Bản ghi ngoài phạm vi trả 404.
- **Lỗi** luôn có dạng `{"detail": "...", "error_code": "...", "errors": [...]}` với mã HTTP 401, 403, 404, 409, 422.
- **Thời gian** theo giờ Việt Nam. Ngày nhận `YYYY-MM-DD` hoặc `DD/MM/YYYY`; thời điểm nhận ISO 8601 (có thể kèm múi giờ) hoặc `DD/MM/YYYY HH:MM`. Tiền là số nguyên (đồng).
- **Tên trường JSON** để tiếng Anh cho dễ ghép với frontend; mọi nội dung hiển thị có thêm trường `*_label` tiếng Việt. Toàn bộ nhãn lấy tại `GET /api/lookups/enums`.
- **Tìm kiếm** không phân biệt hoa thường và dấu: `q=anh duong` tìm được "Ánh Dương".

## 6. Kiểm thử tự động

```powershell
.\chay_kiem_thu.ps1
# hoặc: python -m unittest discover -s tests -t . -v
```

## 7. Đẩy lên GitHub

Giải nén thư mục `crm_backend` vào repo của nhóm, rồi chạy trong PowerShell tại thư mục gốc của repo:

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/SCRUM-87-100-crm-backend
git add crm_backend
git commit -m "SCRUM-87 SCRUM-88 SCRUM-89 SCRUM-90 SCRUM-99 SCRUM-100: backend cơ hội, pipeline, dòng sản phẩm, điều kiện giai đoạn, hoạt động, công việc"
git push -u origin feature/SCRUM-87-100-crm-backend
```

Sau đó tạo Pull Request vào nhánh `develop` trên GitHub. Mã story có trong tên nhánh và nội dung commit nên nếu Jira đã kết nối GitHub, 6 story sẽ tự hiện liên kết tới commit này. File `.gitignore` đã loại bỏ `.venv` và file CSDL.

## 8. Quy tắc nghiệp vụ đã chọn (khi tiêu chí chưa nói rõ)

- **Điều kiện giai đoạn (SCRUM-90)**: chuyển tiến nhảy cóc phải thoả điều kiện của mọi giai đoạn bị bỏ qua; tạo cơ hội thẳng ở giai đoạn sau cũng phải thoả; chuyển lùi hoặc sang "Thua" không bị chặn (trừ điều kiện cấu hình `only_forward: false`). Chỉ hoạt động **đã diễn ra** mới được tính.
- **Xác suất thắng** quay về mặc định của giai đoạn mới mỗi khi chuyển giai đoạn.
- **Đình trệ (SCRUM-88)**: nằm ở giai đoạn lâu hơn ngưỡng của giai đoạn (Tiếp cận 14 ngày, Xác định nhu cầu 14, Đề xuất 21, Báo giá 14, Đàm phán 10) hoặc không có hoạt động trong số ngày đó; quá ngày dự kiến chốt có cảnh báo riêng.
- **Thuê bao (SCRUM-89)**: tổng giá trị = số lượng × đơn giá mỗi kỳ × số kỳ × (1 − chiết khấu); giá trị theo năm = giá trị quy đổi 12 tháng, kèm bảng phân bổ từng năm hợp đồng.
- **Công việc (SCRUM-100)**: muốn lùi hạn phải dùng chức năng Hoãn (bắt buộc lý do); sửa trực tiếp chỉ được đưa hạn sớm hơn.
- **Cơ hội đã đóng** (Thắng/Thua) không sửa thông tin hay dòng sản phẩm được; muốn sửa thì chuyển về giai đoạn đang mở.

## 9. Cấu trúc thư mục

```
crm_backend/
├── app/
│   ├── __init__.py          # tạo ứng dụng, tự đăng ký blueprint của từng story
│   ├── schema.sql           # lược đồ CSDL (đánh dấu bảng theo story)
│   ├── seed.py              # dữ liệu mẫu
│   ├── auth.py, permissions.py, validation.py, errors.py, db.py, clock.py, labels.py, config.py
│   ├── common/              # đăng nhập, tra cứu, truy xuất dùng chung
│   └── features/
│       ├── opportunities/       # SCRUM-87
│       ├── pipeline/            # SCRUM-88
│       ├── opportunity_lines/   # SCRUM-89
│       ├── stage_gates/         # SCRUM-90
│       ├── activities/          # SCRUM-99
│       └── tasks/               # SCRUM-100
├── tests/                   # kiểm thử theo từng story
├── run.py, requirements.txt, chay_server.ps1, chay_kiem_thu.ps1
└── .gitignore, .gitattributes
```
