# SCRUM-85: Chuyß╗ân Lead th├ánh Kh├ích h├áng, Ng╞░ß╗¥i li├¬n hß╗ç v├á C╞í hß╗Öi b├ín h├áng (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story: **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn chuyß╗ân mß╗Öt lead ─æß╗º ─æiß╗üu kiß╗çn th├ánh kh├ích h├áng v├á c╞í hß╗Öi, ─æß╗â kh├┤ng phß║úi nhß║¡p lß║íi th├┤ng tin ─æ├ú hß╗Åi kh├ích ba lß║ºn."**

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Mß╗Öt thao t├íc sinh ─æß╗ông thß╗¥i 3 ─æß╗æi t╞░ß╗úng** | API `POST /api/leads/<id>/convert` tß║ío nguy├¬n tß╗¡: `dbo.customers` + `dbo.lead_contacts` + `dbo.opportunities`. Nß║┐u bß║Ñt kß╗│ b╞░ß╗¢c n├áo lß╗ùi, to├án bß╗Ö rollback. |
| **2. Dß╗» liß╗çu lead chuyß╗ân sang, kh├┤ng nhß║¡p lß║íi** | `convert_lead_to_customer()` tß╗▒ ─æß╗Öng d├╣ng `lead.full_name`, `lead.email`, `lead.phone`, `lead.company` ΓåÆ kh├┤ng cß║ºn frontend truyß╗ün lß║íi. |
| **3. Lead chuyß╗ân sang '─É├ú chuyß╗ân ─æß╗òi' v├á kh├┤ng sß╗¡a ─æ╞░ß╗úc** | `UPDATE dbo.leads SET status='─É├ú chuyß╗ân ─æß╗òi'`. Mß╗ìi thao t├íc sß╗¡a/assign/accept/reject sau ─æ├│ ─æß╗üu raise `ValueError("lead_already_converted")`. |
| **4. To├án bß╗Ö hoß║ít ─æß╗Öng lead ─æ╞░ß╗úc giß╗» lß║íi tr├¬n kh├ích h├áng mß╗¢i** | `convert_lead_to_customer()` nh├ón bß║ún to├án bß╗Ö `dbo.lead_activities` ΓåÆ `dbo.customer_interactions` vß╗¢i tiß╗ün tß╗æ `[Tß╗½ lead #id]`. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-85-lead-convert-to-customer-backend/
Γö£ΓöÇΓöÇ README.md
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_85_lead_convert_to_customer.sql   ΓåÉ Bß║úng leads + lead_contacts
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ leads.py                             ΓåÉ Module Lead (tß╗½ SCRUM-84)
    Γöé   Γö£ΓöÇΓöÇ lead_convert.py                      ΓåÉ Γÿà Module mß╗¢i: Chuyß╗ân ─æß╗òi Lead
    Γöé   ΓööΓöÇΓöÇ routes.py                            ΓåÉ API Endpoints (th├¬m routes SCRUM-85)
    ΓööΓöÇΓöÇ tests/
        ΓööΓöÇΓöÇ test_lead_convert_to_customer.py     ΓåÉ Γÿà Test suite cho SCRUM-85
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Thay ─æß╗òi DB

### Bß║úng mß╗¢i: `dbo.lead_contacts`
L╞░u th├┤ng tin ng╞░ß╗¥i li├¬n hß╗ç (Contact Person) cß╗ºa kh├ích h├áng doanh nghiß╗çp ─æ╞░ß╗úc tß║ío tß╗½ chuyß╗ân ─æß╗òi lead:

| Cß╗Öt | Kiß╗âu | M├┤ tß║ú |
|---|---|---|
| `id` | INT PK | Auto-increment |
| `customer_id` | INT FK | FK ΓåÆ `dbo.customers.id` |
| `lead_id` | INT FK | FK ΓåÆ `dbo.leads.id` (nguß╗ôn gß╗æc) |
| `full_name` | NVARCHAR(255) | T├¬n ng╞░ß╗¥i li├¬n hß╗ç (tß╗½ lead) |
| `email` | NVARCHAR(255) | Email (tß╗½ lead) |
| `phone` | NVARCHAR(50) | Sß╗æ ─æiß╗çn thoß║íi (tß╗½ lead) |
| `position` | NVARCHAR(255) | Chß╗⌐c vß╗Ñ (t├╣y chß╗ìn) |
| `is_primary` | BIT | Lu├┤n = 1 khi tß║ío tß╗½ lead |

---

## ≡ƒôí Chi tiß║┐t API Endpoints (SCRUM-85)

| Method | Endpoint | Quyß╗ün | M├┤ tß║ú |
|---|---|---|---|
| `POST` | `/api/leads/<id>/convert` | All | **Chuyß╗ân ─æß╗òi lead** th├ánh KH + Ng╞░ß╗¥i LH + C╞í hß╗Öi |
| `GET` | `/api/customers/<id>/contacts` | All | Danh s├ích ng╞░ß╗¥i li├¬n hß╗ç cß╗ºa KH |
| *(Thß╗½a kß║┐)* | `/api/leads/*` | | Tß║Ñt cß║ú API SCRUM-84 |

### Request Body cho `/api/leads/<id>/convert`
```json
{
  "company_name": "C├┤ng ty TNHH ABC",        // Nß║┐u bß╗Å trß╗æng, d├╣ng company tß╗½ lead
  "company_phone": "0901234567",               // Nß║┐u bß╗Å trß╗æng, d├╣ng phone tß╗½ lead
  "company_email": "contact@abc.com",          // Nß║┐u bß╗Å trß╗æng, d├╣ng email tß╗½ lead
  "company_address": "123 Nguyß╗àn Huß╗ç, Q.1",
  "opportunity_title": "Dß╗▒ ├ín ERP Q4/2026",   // Nß║┐u bß╗Å trß╗æng, tß╗▒ tß║ío tß╗½ t├¬n lead
  "opportunity_value": 150000000,
  "opportunity_stage": "Tiß║┐p cß║¡n",
  "opportunity_stage_key": "contact",
  "opportunity_expected_close_date": "2026-12-31",
  "contact_position": "Gi├ím ─æß╗æc mua h├áng"
}
```
Response `201`:
```json
{
  "message": "Lead ─æ├ú chuyß╗ân ─æß╗òi th├ánh c├┤ng. Kh├ích h├áng #15, C╞í hß╗Öi #8 ─æ╞░ß╗úc tß║ío.",
  "result": {
    "lead_id": 42,
    "customer_id": 15,
    "opportunity_id": 8,
    "customer_name": "C├┤ng ty TNHH ABC",
    "opportunity_title": "Dß╗▒ ├ín ERP Q4/2026",
    "contact": { "full_name": "Nguyß╗àn V─ân A", "email": "...", "phone": "...", "position": "Gi├ím ─æß╗æc mua h├áng" },
    "converted_at": 1728547200000,
    "activities_migrated": 5
  }
}
```

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng

```powershell
cd backend
.venv\Scripts\pytest tests/test_lead_convert_to_customer.py -v
```
