# SCRUM-86: Danh s├ích Lead vß╗¢i Bß╗Ö lß╗ìc n├óng cao + Bß╗Ö lß╗ìc l╞░u sß║╡n (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story: **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn xem danh s├ích lead vß╗¢i bß╗Ö lß╗ìc v├á bß╗Ö lß╗ìc l╞░u sß║╡n, ─æß╗â mß╗ƒ m├íy buß╗òi s├íng l├á biß║┐t ngay h├┤m nay cß║ºn gß╗ìi ai."**

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Lß╗ìc theo trß║íng th├íi, nguß╗ôn, ph├ón loß║íi n├│ng/ß║Ñm/lß║ính, ng╞░ß╗¥i phß╗Ñ tr├ích, khoß║úng thß╗¥i gian** | API `GET /api/leads/search-filter` nhß║¡n query params: `status`, `source`, `classification` (hot/warm/cold), `assigned_to`, `date_from`, `date_to`. Hß╗ù trß╗ú t├¼m kiß║┐m full-text `q` v├á ph├ón trang. |
| **2. Lead qu├í SLA hiß╗ân thß╗ï nß╗òi bß║¡t** | Mß╗ùi lead trong response k├¿m `sla_status`: `"ok"` / `"warning"` / `"breached"`. Frontend d├╣ng tr╞░ß╗¥ng n├áy ─æß╗â t├┤ m├áu nß╗òi bß║¡t. C├│ thß╗â lß╗ìc `sla_breached_only=true` ─æß╗â chß╗ë xem lead vi phß║ím. |
| **3. L╞░u v├á ─æß║╖t t├¬n cho bß╗Ö lß╗ìc hay d├╣ng** | CRUD API `/api/lead-saved-filters`: tß║ío, ─æß╗ìc, sß╗¡a, x├│a. Ti├¬u ch├¡ l╞░u d╞░ß╗¢i dß║íng JSON. API `GET /api/lead-saved-filters/<id>/apply` ├íp dß╗Ñng ngay bß╗Ö lß╗ìc ─æ├ú l╞░u. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-86-lead-filter-saved-backend/
Γö£ΓöÇΓöÇ README.md
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_86_lead_filter_saved.sql           ΓåÉ Bß║úng leads + lead_saved_filters
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ leads.py                             ΓåÉ Module Lead (tß╗½ SCRUM-84)
    Γöé   Γö£ΓöÇΓöÇ lead_filters.py                      ΓåÉ Γÿà Module mß╗¢i: Bß╗Ö lß╗ìc Lead + Saved Filters
    Γöé   ΓööΓöÇΓöÇ routes.py                            ΓåÉ API Endpoints (th├¬m routes SCRUM-86)
    ΓööΓöÇΓöÇ tests/
        ΓööΓöÇΓöÇ test_lead_filter_saved.py            ΓåÉ Γÿà Test suite cho SCRUM-86
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Thay ─æß╗òi DB

### Bß║úng mß╗¢i: `dbo.lead_saved_filters`
L╞░u bß╗Ö lß╗ìc lead cß╗ºa tß╗½ng nh├ón vi├¬n:

| Cß╗Öt | Kiß╗âu | M├┤ tß║ú |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `user_id` | INT FK | Chß╗º sß╗ƒ hß╗»u bß╗Ö lß╗ìc |
| `name` | NVARCHAR(255) | T├¬n gß╗úi nhß╗¢: "Leads n├│ng tuß║ºn n├áy", "Cß║ºn gß╗ìi h├┤m nay" |
| `criteria_json` | NVARCHAR(MAX) | JSON chß╗⌐a c├íc ti├¬u ch├¡ lß╗ìc |
| `created_at`, `updated_at` | BIGINT | Timestamp Unix ms |

---

## ≡ƒôí Chi tiß║┐t API Endpoints (SCRUM-86)

### Bß╗Ö lß╗ìc Lead n├óng cao
| Method | Endpoint | Quyß╗ün | M├┤ tß║ú |
|---|---|---|---|
| `GET` | `/api/leads/search-filter` | All | **Lß╗ìc lead** theo nhiß╗üu ─æiß╗üu kiß╗çn + SLA nß╗òi bß║¡t |

**Query params hß╗ù trß╗ú:**
| Param | Kiß╗âu | M├┤ tß║ú |
|---|---|---|
| `q` | string | T├¼m kiß║┐m theo t├¬n, email, phone, c├┤ng ty |
| `status` | string | `Mß╗¢i` / `─É├ú ph├ón c├┤ng` / `─Éang ch─âm s├│c` / `Chß╗¥ ph├ón bß╗ò` |
| `source` | string | Nguß╗ôn lead (Facebook, Website, Zalo...) |
| `classification` | string | `hot` / `warm` / `cold` |
| `assigned_to` | int | ID nh├ón vi├¬n phß╗Ñ tr├ích |
| `date_from` | int | Unix ms - tß╗½ ng├áy tß║ío |
| `date_to` | int | Unix ms - ─æß║┐n ng├áy tß║ío |
| `sla_breached_only` | bool | `true` = chß╗ë hiß╗çn lead vi phß║ím SLA |
| `sort_by` | string | `created_at` / `sla_deadline_at` / `status` / `classification` |
| `order` | string | `asc` / `desc` |
| `page`, `per_page` | int | Ph├ón trang |

### Bß╗Ö lß╗ìc ─æ├ú l╞░u sß║╡n
| Method | Endpoint | Quyß╗ün | M├┤ tß║ú |
|---|---|---|---|
| `GET` | `/api/lead-saved-filters` | All | Danh s├ích bß╗Ö lß╗ìc ─æ├ú l╞░u cß╗ºa user |
| `POST` | `/api/lead-saved-filters` | All | **L╞░u bß╗Ö lß╗ìc** vß╗¢i t├¬n gß╗úi nhß╗¢ |
| `GET` | `/api/lead-saved-filters/<id>` | All | Chi tiß║┐t bß╗Ö lß╗ìc |
| `PUT` | `/api/lead-saved-filters/<id>` | All | Cß║¡p nhß║¡t t├¬n/ti├¬u ch├¡ |
| `DELETE` | `/api/lead-saved-filters/<id>` | All | X├│a bß╗Ö lß╗ìc |
| `GET` | `/api/lead-saved-filters/<id>/apply` | All | **├üp dß╗Ñng bß╗Ö lß╗ìc** ΓåÆ trß║ú vß╗ü danh s├ích lead |

### V├¡ dß╗Ñ: L╞░u bß╗Ö lß╗ìc "Leads n├│ng cß║ºn gß╗ìi h├┤m nay"
```http
POST /api/lead-saved-filters
{
  "name": "Leads n├│ng cß║ºn gß╗ìi h├┤m nay",
  "criteria": {
    "classification": "hot",
    "status": "─Éang ch─âm s├│c",
    "assigned_to": 5,
    "sort_by": "sla_deadline_at",
    "order": "asc"
  }
}
```
Response `201`:
```json
{
  "message": "L╞░u bß╗Ö lß╗ìc lead th├ánh c├┤ng.",
  "saved_filter": {
    "id": 3,
    "name": "Leads n├│ng cß║ºn gß╗ìi h├┤m nay",
    "criteria": { "classification": "hot", "status": "─Éang ch─âm s├│c", ... }
  }
}
```

### V├¡ dß╗Ñ: ├üp dß╗Ñng bß╗Ö lß╗ìc ─æ├ú l╞░u
```http
GET /api/lead-saved-filters/3/apply?page=1&per_page=20
```
ΓåÆ Trß║ú vß╗ü danh s├ích lead ph├╣ hß╗úp vß╗¢i ti├¬u ch├¡ ─æ├ú l╞░u, k├¿m `sla_status` cho tß╗½ng lead.

### sla_status trong response
```json
{
  "sla_status": "breached",   // ΓåÉ Frontend t├┤ ─æß╗Å nß╗òi bß║¡t
  "sla_deadline_at": 1728547200000
}
```
| Gi├í trß╗ï | ├¥ ngh─⌐a | Frontend |
|---|---|---|
| `"ok"` | SLA c├▓n > 8 giß╗¥ | Xanh/b├¼nh th╞░ß╗¥ng |
| `"warning"` | SLA c├▓n < 8 giß╗¥ | V├áng cß║únh b├ío |
| `"breached"` | ─É├ú v╞░ß╗út SLA | ─Éß╗Å nß╗òi bß║¡t |
| `"not_assigned"` | Ch╞░a ph├ón c├┤ng | X├ím |

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_filter_saved.py -v
```
