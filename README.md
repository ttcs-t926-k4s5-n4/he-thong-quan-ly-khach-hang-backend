# CRM – Lead & Marketing (Epic SCRUM-19) — chỉ Backend

Bộ mã backend cho 3 user story thuộc epic **SCRUM-19**, viết song song bằng **Python (Flask + SQLite)** và **Node.js (không cần cài thư viện)**. Hai bản có **cùng API, cùng tiêu chí chấp nhận, cùng bộ test**, nên nhóm có thể chọn bản nào cũng được.

| Story | Nhánh Git | Python | Node.js |
|---|---|---|---|
| SCRUM-78 – Thu thập lead từ biểu mẫu nhúng | `feature/SCRUM-78-lead-web-form-backend` | `app/features/scrum78_web_form.py` | `src/features/scrum78-web-form.js` |
| SCRUM-79 – Tạo lead thủ công & nhập Excel | `feature/SCRUM-79-lead-import-excel-backend` | `app/features/scrum79_lead_import.py` | `src/features/scrum79-lead-import.js` |
| SCRUM-80 – Theo dõi lead theo chiến dịch | `feature/SCRUM-80-campaign-tracking-backend` | `app/features/scrum80_campaign_tracking.py` | `src/features/scrum80-campaign-tracking.js` |

Phần **lõi dùng chung** (CSDL, kiểm tra dữ liệu, API xem/sửa lead) nằm ở `python-backend/app/core.py` và `nodejs-backend/src/core/`. Mỗi feature là một module độc lập: nhánh nào chỉ có 1 feature thì server vẫn chạy và chỉ nạp feature đó (xem `/health`).

---

## 1. Chạy thử trong VS Code

Mở thư mục `crm-lead-marketing` bằng VS Code → **Terminal → New Terminal**.

### 1.1 Bản Python (cổng 8000) — cần Python ≥ 3.9

**Windows (PowerShell):**
```powershell
cd python-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```
> Nếu PowerShell báo lỗi "running scripts is disabled", chạy trước: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**macOS / Linux:**
```bash
cd python-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Chạy test (mở terminal thứ 2, kích hoạt lại `.venv`):
```bash
cd python-backend
python -m unittest discover -s tests -t . -v
```

### 1.2 Bản Node.js (cổng 3000) — cần Node.js ≥ 18.17, KHÔNG cần `npm install`

```bash
cd nodejs-backend
npm start          # hoặc: node src/server.js
npm run dev        # tự khởi động lại khi sửa code
npm test           # chạy toàn bộ test
```

### 1.3 Kiểm tra nhanh
- Mở trình duyệt: `http://127.0.0.1:8000/health` (Python) hoặc `http://127.0.0.1:3000/health` (Node).
- Cài extension **REST Client** (humao.rest-client) rồi mở `requests.http`, bấm **Send Request** trên từng request theo thứ tự.
- Xem biểu mẫu nhúng hoạt động: tạo form → mở `http://127.0.0.1:8000/embed/<public_key>/page`, đợi > 3 giây rồi bấm Gửi.

### 1.4 Biến môi trường (tuỳ chọn)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `PORT` / `HOST` | 8000 (Py), 3000 (Node) / 127.0.0.1 | Cổng & địa chỉ server |
| `DB_PATH` | `data/crm_leads.db` (Py), `data/crm_leads.json` (Node) | Nơi lưu dữ liệu |
| `PUBLIC_BASE_URL` | lấy theo request | URL công khai dùng trong mã nhúng (VD `https://crm.congty.vn`) |
| `TRUST_PROXY` | 0 | `1` nếu chạy sau Nginx/Cloudflare để lấy IP thật từ `X-Forwarded-For` |
| `RATE_LIMIT_PER_FORM` | `5/600` | Tối đa 5 lần gửi / 10 phút / IP / biểu mẫu |
| `RATE_LIMIT_PER_IP` | `20/3600` | Tối đa 20 lần gửi / giờ / IP cho mọi biểu mẫu |
| `MIN_FILL_SECONDS` | 3 | Gửi nhanh hơn số giây này sau khi form hiện ra → coi là bot |
| `MAX_IMPORT_ROWS` | 2000 | Số dòng tối đa mỗi lần nhập Excel |
| `IMPORT_PREVIEW_TTL_MINUTES` | 30 | Thời hạn bản xem trước trước khi xác nhận nhập |

---

## 2. Tạo nhánh cho từng story & đẩy lên GitHub

Chép thư mục `crm-lead-marketing` vào trong repo của nhóm (repo đã có nhánh `develop`), rồi chạy **một** trong hai script dưới đây. Script sẽ tạo 3 nhánh từ `develop`, mỗi nhánh gồm phần lõi + đúng 1 feature + test của feature đó, và commit sẵn.

**Windows (PowerShell):**
```powershell
cd crm-lead-marketing
powershell -ExecutionPolicy Bypass -File .\scripts\tao-nhanh-feature.ps1          # chỉ tạo nhánh + commit
powershell -ExecutionPolicy Bypass -File .\scripts\tao-nhanh-feature.ps1 -Push    # tạo + đẩy lên origin
```

**Git Bash / macOS / Linux:**
```bash
cd crm-lead-marketing
bash scripts/tao-nhanh-feature.sh          # chỉ tạo nhánh + commit
bash scripts/tao-nhanh-feature.sh --push   # tạo + đẩy lên origin
```

Làm tay cho một nhánh (ví dụ SCRUM-78):
```bash
git checkout develop && git pull
git checkout -b feature/SCRUM-78-lead-web-form-backend
git add crm-lead-marketing/            # hoặc chỉ các file của SCRUM-78 + lõi
git commit -m "feat(SCRUM-78): backend thu thập lead từ biểu mẫu nhúng"
git push -u origin feature/SCRUM-78-lead-web-form-backend
```
Sau đó tạo Pull Request từ từng nhánh vào `develop`.

---

## 3. Chức năng & tiêu chí đánh giá (Acceptance Criteria)

Mỗi tiêu chí có mã `AC78-xx`, `AC79-xx`, `AC80-xx` trùng với tên test tự động, nên kết quả `unittest` / `npm test` chính là bằng chứng nghiệm thu.

### SCRUM-78 — Thu thập lead từ biểu mẫu nhúng trên website

> *Là Nhân viên Marketing, tôi muốn thu thập lead từ biểu mẫu nhúng trên website, để mọi lead vào thẳng hệ thống thay vì nằm trong hộp thư chung.*

**Chức năng**

1. Quản lý biểu mẫu: tạo, xem danh sách (kèm số lead đã thu), xem chi tiết, sửa, bật/tắt. Mỗi biểu mẫu có thể gắn một chiến dịch và danh sách tên miền được phép.
2. Sinh mã nhúng theo 2 cách: thẻ `<script>` (vẽ form ngay trong trang) hoặc `<iframe>`; dán được vào website bất kỳ (WordPress, Landing page, HTML tĩnh).
3. Form gồm: Họ tên*, Email*, Số điện thoại*, Công ty, Nhu cầu quan tâm; hiển thị lỗi ngay dưới từng ô.
4. Chống spam nhiều lớp: trường bẫy ẩn (honeypot), bẫy thời gian (gửi < 3 giây), kiểm tra domain nguồn, giới hạn tần suất theo IP (trả `429` + `Retry-After`).
5. Gửi thành công → tạo lead trạng thái **Mới**, nguồn `web_form`, gắn `form_id`, `campaign_id` của biểu mẫu, lưu IP.

| Mã | Tiêu chí (Given / When / Then) |
|---|---|
| AC78-01 | Khi tạo biểu mẫu hợp lệ, hệ thống trả `201` kèm `public_key`, mã nhúng `script`, `iframe` và `submit_url`. |
| AC78-02 | `GET /embed/{key}.js` trả JavaScript có đủ 5 trường và trường honeypot; `GET /embed/{key}/page` trả trang HTML dùng cho iframe. |
| AC78-03 | Gửi dữ liệu hợp lệ → `201`, tạo đúng 1 lead với `status = "Mới"`, `source = "web_form"`, `form_id`, `campaign_id` đúng của biểu mẫu; SĐT được chuẩn hoá về `0xxxxxxxxx`. |
| AC78-04 | Thiếu họ tên, email sai, SĐT sai → `422`, `details` chỉ rõ từng trường lỗi; không tạo lead. |
| AC78-05 | Trường honeypot có giá trị → trả `201` (để bot không biết) nhưng **không** tạo lead. |
| AC78-06 | Gửi khi form mới hiện < `MIN_FILL_SECONDS` giây → không tạo lead; gửi sau ≥ 3 giây → tạo lead. |
| AC78-07 | Cùng IP gửi lần thứ 6 trong 10 phút vào cùng biểu mẫu → `429` có header `Retry-After`; IP khác vẫn gửi được. |
| AC78-08 | Biểu mẫu có `allowed_domains` → gửi từ domain lạ bị `403`; gửi từ domain/subdomain được phép → `201`. Domain nhập dạng URL được tự chuẩn hoá. |
| AC78-09 | Biểu mẫu bị tắt (`is_active = false`) → gửi dữ liệu nhận `404`. |
| AC78-10 | Tạo biểu mẫu thiếu tên / domain sai / chiến dịch không tồn tại → `422` chỉ rõ từng trường. |

### SCRUM-79 — Tạo lead thủ công và nhập lead hàng loạt từ Excel

> *Là Nhân viên Marketing, tôi muốn tạo lead thủ công và nhập lead hàng loạt từ Excel, để đưa danh sách thu được từ hội thảo vào hệ thống ngay hôm sau.*

**Chức năng**

1. Nhập tay một lead từ sự kiện hoặc danh thiếp: họ tên, email/SĐT, công ty, nhu cầu, ghi chú, **nguồn (bắt buộc)**, chi tiết nguồn (tên sự kiện), chiến dịch. Phát hiện trùng email/SĐT (trả `409`, cho phép ghi đè bằng `allow_duplicate=true`).
2. Tải tệp mẫu `mau-nhap-lead.xlsx` (sheet dữ liệu + sheet hướng dẫn liệt kê nguồn hợp lệ).
3. Nhập hàng loạt 2 bước:
   - **Xem trước**: tải .xlsx/.csv, chọn nguồn mặc định, chi tiết nguồn, chiến dịch → hệ thống đọc, chuẩn hoá và báo lỗi **theo từng dòng** (số dòng đúng như trong Excel), **chưa ghi** vào CSDL.
   - **Xác nhận**: `valid_only` (nhập dòng đúng, bỏ dòng lỗi) hoặc `all_or_nothing` (còn lỗi thì không nhập gì). Mỗi lô chỉ xác nhận được 1 lần, bản xem trước hết hạn sau 30 phút.
4. Nhận diện cột linh hoạt (có dấu/không dấu, "SĐT"/"Số điện thoại"...), tự thêm số 0 bị Excel làm mất ở SĐT, nhận nguồn theo tên tiếng Việt hoặc mã.
5. Mọi lead nhập vào đều có nguồn: lấy từ cột "Nguồn" của dòng, nếu trống thì dùng nguồn mặc định của lô; không có cả hai → dòng bị báo lỗi.

| Mã | Tiêu chí |
|---|---|
| AC79-01 | Nhập tay lead có nguồn "Danh thiếp" → `201`, trạng thái **Mới**, nguồn lưu mã `danh_thiep`, SĐT `+84...` chuẩn hoá về `0...`, ghi nhận người tạo từ header `X-User-Id`. |
| AC79-02 | Nhập tay thiếu nguồn hoặc dùng nguồn `web_form` → `422`. |
| AC79-03 | Không có cả email lẫn SĐT → `422` (trường `contact`). |
| AC79-04 | Trùng email/SĐT với lead đã có (không phân biệt hoa thường) → `409` kèm `duplicate_lead_id`; gửi `allow_duplicate=true` → tạo được. |
| AC79-05 | Tải tệp mẫu → tệp .xlsx hợp lệ, dòng 1 là tiêu đề bắt đầu bằng "Họ tên*", có cột "Nguồn", có sheet hướng dẫn. |
| AC79-06 | Xem trước tệp có dòng thiếu tên, email sai, trùng trong tệp, trùng trong hệ thống, nguồn sai → mỗi dòng lỗi được báo đúng số dòng Excel và lý do; dòng đúng được chuẩn hoá; CSDL không thay đổi. |
| AC79-07 | Xác nhận lô → chỉ nhập dòng hợp lệ, mọi lead có nguồn, gắn đúng chiến dịch và `import_batch_id`, trạng thái **Mới**; xác nhận lần 2 → `409`. |
| AC79-08 | Không có cột Nguồn và không chọn nguồn mặc định → dòng bị lỗi ở trường `source`. |
| AC79-09 | Chế độ `all_or_nothing` khi còn dòng lỗi → `422`, không lead nào được tạo. |
| AC79-10 | Tệp sai định dạng, thiếu cột "Họ tên", hoặc không có dòng dữ liệu → `400` với thông báo rõ ràng. |
| AC79-11 | Hỗ trợ CSV UTF-8 (dấu phân cách `,` `;` hoặc tab). |

### SCRUM-80 — Theo dõi lead theo từng chiến dịch

> *Là Nhân viên Marketing, tôi muốn theo dõi lead theo từng chiến dịch, để đo được chiến dịch nào thực sự ra doanh thu chứ không chỉ ra nhiều lead.*

**Chức năng**

1. Khai báo chiến dịch: tên (duy nhất), kênh (`facebook`, `google_ads`, `email`, `zalo`, `website`, `su_kien`, `hoi_thao`, `khac`), ngân sách, ngày bắt đầu – kết thúc, mô tả. Trạng thái tự tính: Sắp chạy / Đang chạy / Đã kết thúc.
2. Liên kết cố định: lead mang `campaign_id` từ biểu mẫu/lô nhập/nhập tay; chuyển đổi lead → cơ hội thì cơ hội **kế thừa** chiến dịch của lead; không API nào cho sửa chiến dịch gốc của lead hay cơ hội.
3. Quản lý cơ hội: tạo, xem, cập nhật giai đoạn (Mới → Đang đàm phán → Thắng/Thua) và giá trị; cơ hội Thắng bắt buộc có giá trị > 0, tự ghi `closed_at`.
4. Báo cáo từng chiến dịch: số lead, số lead đã chuyển đổi, số cơ hội (mở/thắng/thua), **giá trị đã chốt**, giá trị pipeline, tỷ lệ lead→cơ hội, tỷ lệ thắng, chi phí/lead, chi phí/deal thắng, **ROI**, lead theo nguồn.
5. Báo cáo tổng hợp: xếp hạng chiến dịch theo doanh thu (mặc định) hoặc ROI/số lead…, lọc theo kênh và khoảng thời gian, chỉ ra chiến dịch nhiều lead nhất vs chiến dịch ra doanh thu cao nhất, thống kê lead không thuộc chiến dịch.

| Mã | Tiêu chí |
|---|---|
| AC80-01 | Tạo chiến dịch đủ tên, kênh, ngân sách, thời gian → `201`, có `channel_label` và `status`. |
| AC80-02 | Thiếu tên, kênh sai, ngân sách âm, ngày kết thúc trước ngày bắt đầu → `422` chỉ rõ từng trường; trùng tên → `409`. |
| AC80-03 | Sửa ngân sách thành công; sửa làm ngày kết thúc < ngày bắt đầu → `422`. |
| AC80-04 | Chuyển đổi lead → cơ hội có `campaign_id` = chiến dịch của lead, lead chuyển sang "Đã chuyển đổi"; chuyển đổi lần 2 → `409`. |
| AC80-05 | Mọi thao tác cố đổi chiến dịch gốc (sửa lead, gửi `campaign_id` khi chuyển đổi, sửa cơ hội, tạo cơ hội với chiến dịch khác chiến dịch của lead) → `422`. |
| AC80-06 | Chuyển cơ hội sang "Thắng" mà giá trị = 0 → `422`; có giá trị → `200`, `is_closed = true`, có `closed_at`. |
| AC80-07 | Báo cáo chiến dịch tính đúng số lead, số cơ hội, giá trị đã chốt, pipeline, chi phí/lead, tỷ lệ thắng, ROI = (doanh thu − ngân sách) / ngân sách × 100. |
| AC80-08 | Chiến dịch A có 10 lead nhưng doanh thu 5 triệu, chiến dịch B có 3 lead nhưng doanh thu 100 triệu → báo cáo tổng xếp B trên A, `top_by_revenue = B`, `top_by_leads = A`, có câu `insight`; `sort=lead_count` thì A đứng đầu. |
| AC80-09 | Xem danh sách lead của một chiến dịch chỉ trả lead thuộc chiến dịch đó. |

### Tiêu chí chung (Definition of Done)

- Toàn bộ thông báo lỗi bằng tiếng Việt, định dạng thống nhất: `{"error": {"status", "message", "details"}}`.
- Mọi lead đều có nguồn — được ép ở cả tầng code (hàm tạo lead duy nhất) và tầng CSDL (`CHECK` trên cột `source` ở bản Python).
- Test tự động cho mọi AC chạy xanh ở cả hai bản; mỗi nhánh feature chạy độc lập được.
- Có CORS để website bên ngoài gọi được endpoint công khai.

---

## 4. Danh sách API

| Phương thức | Đường dẫn | Story | Mô tả |
|---|---|---|---|
| GET | `/health` | lõi | Trạng thái & các feature đã nạp |
| GET | `/api/meta` | lõi | Danh mục nguồn, trạng thái, kênh, giai đoạn |
| GET | `/api/leads` | lõi | Danh sách lead (lọc `status, source, campaign_id, form_id, import_batch_id, q`, phân trang) |
| GET / PATCH | `/api/leads/{id}` | lõi | Xem / sửa trạng thái, công ty, nhu cầu, ghi chú |
| POST | `/api/forms` | 78 | Tạo biểu mẫu |
| GET | `/api/forms`, `/api/forms/{id}` | 78 | Danh sách / chi tiết |
| PATCH | `/api/forms/{id}` | 78 | Sửa, bật/tắt |
| GET | `/api/forms/{id}/embed-code` | 78 | Lấy mã nhúng |
| GET | `/embed/{key}.js`, `/embed/{key}/page` | 78 | Script & trang iframe (công khai) |
| POST | `/public/forms/{key}/submit` | 78 | Nhận dữ liệu form (công khai) |
| POST | `/api/leads` | 79 | Nhập tay một lead |
| GET | `/api/leads/import/template` | 79 | Tải tệp mẫu |
| POST | `/api/leads/import/preview` | 79 | Tải tệp + xem trước (multipart: `file`, `default_source`, `source_detail`, `campaign_id`) |
| GET | `/api/leads/import/{id}` | 79 | Xem lại lô nhập |
| POST | `/api/leads/import/{id}/commit` | 79 | Xác nhận nhập (`mode`: `valid_only` / `all_or_nothing`) |
| POST / GET | `/api/campaigns` | 80 | Tạo / danh sách chiến dịch |
| GET / PATCH | `/api/campaigns/{id}` | 80 | Chi tiết (kèm số liệu) / sửa |
| GET | `/api/campaigns/{id}/leads` | 80 | Lead của chiến dịch |
| GET | `/api/campaigns/{id}/report` | 80 | Báo cáo một chiến dịch |
| GET | `/api/reports/campaigns` | 80 | Báo cáo tổng hợp (`sort`, `channel`, `from`, `to`) |
| POST | `/api/leads/{id}/convert` | 80 | Chuyển đổi lead → cơ hội |
| POST / GET | `/api/opportunities` | 80 | Tạo / danh sách cơ hội |
| GET / PATCH | `/api/opportunities/{id}` | 80 | Xem / cập nhật giai đoạn, giá trị |

Header tuỳ chọn `X-User-Id` để ghi nhận người tạo (khi ghép với module đăng nhập của nhóm, thay bằng user lấy từ token).

## 5. Cấu trúc thư mục

```
crm-lead-marketing/
├── README.md                 ← tài liệu này
├── requests.http             ← bộ request mẫu cho REST Client
├── scripts/                  ← script tạo nhánh feature/SCRUM-xx
├── python-backend/
│   ├── run.py, requirements.txt
│   ├── app/__init__.py       ← tạo app, nạp feature
│   ├── app/core.py           ← lõi: CSDL, validate, API lead
│   ├── app/features/         ← scrum78 / scrum79 / scrum80
│   └── tests/                ← test theo AC
└── nodejs-backend/
    ├── package.json
    ├── src/server.js, src/app.js
    ├── src/core/             ← constants, db, http, utils, xlsx, leads
    ├── src/features/         ← scrum78 / scrum79 / scrum80
    └── test/                 ← test theo AC
```
