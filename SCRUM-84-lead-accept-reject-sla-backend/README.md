# SCRUM-84: Nhß║¡n/Tß╗½ chß╗æi Lead vß╗¢i r├áng buß╗Öc SLA phß║ún hß╗ôi (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story: **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn nhß║¡n hoß║╖c tß╗½ chß╗æi lead ─æ╞░ß╗úc ph├ón, c├│ r├áng buß╗Öc SLA phß║ún hß╗ôi, ─æß╗â lead kh├┤ng nß║▒m im ba ng├áy rß╗ôi nguß╗Öi hß║│n."**

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Nhß║¡n lead ΓåÆ chuyß╗ân sang ─Éang ch─âm s├│c** | API `POST /api/leads/<id>/accept` ΓÇö chß╗ë nh├ón vi├¬n ─æ╞░ß╗úc ph├ón c├┤ng; cß║¡p nhß║¡t `status = '─Éang ch─âm s├│c'` + ghi activity. |
| **2. Tß╗½ chß╗æi bß║»t buß╗Öc nhß║¡p l├╜ do** | API `POST /api/leads/<id>/reject` ΓÇö validate `reason` bß║»t buß╗Öc; trß║ú 400 nß║┐u thiß║┐u; lead quay vß╗ü `status = 'Chß╗¥ ph├ón bß╗ò'`, t─âng `rejection_count`. |
| **3. Qu├í SLA ΓåÆ gß║»n cß╗¥ & b├ío tr╞░ß╗ƒng nh├│m** | `check_and_flag_sla_breached_leads()` qu├⌐t lead `status='─É├ú ph├ón c├┤ng'` qu├í `sla_deadline_at`, gß║»n `sla_breached=1`, ghi activity cß║únh b├ío. API `GET /api/leads/sla-breached` + `POST /api/leads/check-sla` d├ánh cho manager. |
| **4. SLA t├¡nh tß╗½ thß╗¥i ─æiß╗âm ph├ón c├┤ng** | `assign_lead()` ghi `assigned_at = now` v├á `sla_deadline_at = assigned_at + 3 ng├áy (ms)`. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-84-lead-accept-reject-sla-backend/
Γö£ΓöÇΓöÇ README.md
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_84_lead_accept_reject_sla.sql     ΓåÉ Bß║úng leads + lead_activities
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ leads.py                             ΓåÉ Γÿà Module mß╗¢i: V├▓ng ─æß╗¥i Lead + SLA
    Γöé   ΓööΓöÇΓöÇ routes.py                            ΓåÉ API Endpoints (th├¬m routes SCRUM-84)
    ΓööΓöÇΓöÇ tests/
        ΓööΓöÇΓöÇ test_lead_accept_reject_sla.py       ΓåÉ Γÿà Test suite cho SCRUM-84
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Thay ─æß╗òi DB

### Bß║úng mß╗¢i: `dbo.leads`
| Cß╗Öt | Kiß╗âu | M├┤ tß║ú |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `full_name` | NVARCHAR(255) | T├¬n lead (bß║»t buß╗Öc) |
| `email`, `phone`, `company` | NVARCHAR | Th├┤ng tin li├¬n hß╗ç |
| `source` | NVARCHAR(100) | Nguß╗ôn: Facebook, Zalo, Website... |
| `classification` | VARCHAR(10) | `hot` / `warm` / `cold` |
| `status` | NVARCHAR(50) | `Mß╗¢i` / `─É├ú ph├ón c├┤ng` / `─Éang ch─âm s├│c` / `Chß╗¥ ph├ón bß╗ò` / `─É├ú chuyß╗ân ─æß╗òi` |
| `assigned_to` | INT FK | Nh├ón vi├¬n ─æ╞░ß╗úc ph├ón c├┤ng |
| `assigned_at` | BIGINT | Unix ms khi ph├ón c├┤ng |
| `sla_deadline_at` | BIGINT | `assigned_at + 3 ng├áy` |
| `sla_breached` | BIT | 1 = ─æ├ú vi phß║ím SLA |
| `sla_alert_sent` | BIT | 1 = ─æ├ú gß╗¡i cß║únh b├ío |
| `rejection_reason` | NVARCHAR(1000) | L├╜ do tß╗½ chß╗æi (bß║»t buß╗Öc khi reject) |
| `rejection_count` | INT | Sß╗æ lß║ºn bß╗ï tß╗½ chß╗æi |

### Bß║úng mß╗¢i: `dbo.lead_activities`
Ghi lß╗ïch sß╗¡ mß╗ìi h├ánh ─æß╗Öng tr├¬n lead: `created` / `assigned` / `accepted` / `rejected` / `sla_breached` / `converted` / `updated`.

---

## ≡ƒôí Chi tiß║┐t API Endpoints (SCRUM-84)

| Method | Endpoint | Quyß╗ün | M├┤ tß║ú |
|---|---|---|---|
| `GET` | `/api/leads` | All | Danh s├ích lead (nh├ón vi├¬n chß╗ë thß║Ñy cß╗ºa m├¼nh) |
| `POST` | `/api/leads` | All | Tß║ío lead mß╗¢i |
| `GET` | `/api/leads/<id>` | All | Chi tiß║┐t lead |
| `PUT` | `/api/leads/<id>` | All | Cß║¡p nhß║¡t th├┤ng tin lead |
| `DELETE` | `/api/leads/<id>` | admin/manager | X├│a lead |
| `POST` | `/api/leads/<id>/assign` | admin/manager | Ph├ón c├┤ng lead cho nh├ón vi├¬n |
| `POST` | `/api/leads/<id>/accept` | employee | **Nhß║¡n lead** ΓåÆ ─Éang ch─âm s├│c |
| `POST` | `/api/leads/<id>/reject` | employee | **Tß╗½ chß╗æi lead** (bß║»t buß╗Öc nhß║¡p l├╜ do) |
| `GET` | `/api/leads/sla-breached` | admin/manager | Danh s├ích lead vi phß║ím SLA |
| `POST` | `/api/leads/check-sla` | admin/manager | Qu├⌐t & gß║»n cß╗¥ SLA vi phß║ím |
| `GET` | `/api/leads/<id>/activities` | All | Lß╗ïch sß╗¡ hoß║ít ─æß╗Öng cß╗ºa lead |

### V├¡ dß╗Ñ: Tß╗½ chß╗æi lead
```http
POST /api/leads/42/reject
Content-Type: application/json
{ "reason": "Kh├ích h├áng kh├┤ng ─æ├║ng ph├ón kh├║c mß╗Ñc ti├¬u" }
```
Response `200`:
```json
{
  "message": "─É├ú tß╗½ chß╗æi lead. Lead quay vß╗ü h├áng chß╗¥ ph├ón bß╗ò.",
  "lead": { "id": 42, "status": "Chß╗¥ ph├ón bß╗ò", "rejection_count": 1, ... }
}
```
Thiß║┐u `reason` ΓåÆ Response `400`:
```json
{
  "message": "Vui l├▓ng nhß║¡p l├╜ do tß╗½ chß╗æi.",
  "errors": { "reason": "L├╜ do tß╗½ chß╗æi l├á bß║»t buß╗Öc." }
}
```

### V├¡ dß╗Ñ: SLA Status trong response
```json
{
  "sla_status": "breached",   // "ok" | "warning" | "breached" | "not_assigned"
  "sla_deadline_at": 1728547200000
}
```

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_accept_reject_sla.py -v
```
