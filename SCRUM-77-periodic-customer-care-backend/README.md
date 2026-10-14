# SCRUM-77: Ch─âm s├│c Kh├ích h├áng ─Éß╗ïnh kß╗│ & Lß╗ïch sß╗¡ T╞░╞íng t├íc (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy cung cß║Ñp t├¡nh n─âng **Danh s├ích Ch─âm s├│c ─Éß╗ïnh kß╗│** ΓÇö tß╗▒ ─æß╗Öng liß╗çt k├¬ c├íc kh├ích h├áng ch╞░a ─æ╞░ß╗úc li├¬n hß╗ç trong N ng├áy gß║ºn nhß║Ñt, ╞░u ti├¬n theo gi├í trß╗ï hß╗úp ─æß╗ông. Nh├ón vi├¬n c├│ thß╗â **Ghi nhß║¡n t╞░╞íng t├íc** trß╗▒c tiß║┐p v├á hß╗ç thß╗æng tß╗▒ ─æß╗Öng cß║¡p nhß║¡t thß╗¥i ─æiß╗âm li├¬n hß╗ç gß║ºn nhß║Ñt ─æß╗â theo d├╡i li├¬n tß╗Ñc.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Danh s├ích Ch─âm s├│c ─Éß╗ïnh kß╗│** | API `GET /api/customers/periodic-care?days=30` trß║ú vß╗ü kh├ích h├áng ch╞░a c├│ t╞░╞íng t├íc trong N ng├áy, sß║»p xß║┐p ╞░u ti├¬n theo tß╗òng gi├í trß╗ï c╞í hß╗Öi (`total_contract_value DESC`). |
| **2. Ghi nhß║¡n T╞░╞íng t├íc** | API `POST /api/customers/<id>/interactions` l╞░u bß║ún ghi t╞░╞íng t├íc v├áo `dbo.customer_interactions` v├á tß╗▒ ─æß╗Öng cß║¡p nhß║¡t `last_interaction_at` tr├¬n bß║úng `dbo.customers`. |
| **3. ─É├ính dß║Ñu ─É├ú li├¬n hß╗ç Nhanh** | API `POST /api/customers/<id>/mark-contacted` cho ph├⌐p ─æ├ính dß║Ñu ─æ├ú li├¬n hß╗ç ngay tß╗½ danh s├ích ch─âm s├│c ─æß╗ïnh kß╗│ vß╗¢i 1 thao t├íc. |
| **4. Xem Lß╗ïch sß╗¡ T╞░╞íng t├íc** | API `GET /api/customers/<id>/interactions` trß║ú vß╗ü to├án bß╗Ö lß╗ïch sß╗¡ t╞░╞íng t├íc cß╗ºa 1 kh├ích h├áng, sß║»p xß║┐p mß╗¢i nhß║Ñt l├¬n tr├¬n. |
| **5. Ph├ón trang & Th├┤ng tin bß╗ò sung** | Response tß╗▒ ─æß╗Öng t├¡nh to├ín `days_without_interaction` (sß╗æ ng├áy ch╞░a t╞░╞íng t├íc), `contract_value` v├á gß║»n th├¬m Custom Fields cho tß╗½ng kh├ích h├áng. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-77-periodic-care-backend/
Γö£ΓöÇΓöÇ README.md                               ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_77_periodic_care.sql          ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ periodic_care.py                ΓåÉ Γÿà Module mß╗¢i: Danh s├ích ─æß╗ïnh kß╗│ & T╞░╞íng t├íc
    Γöé   Γö£ΓöÇΓöÇ customers.py                    ΓåÉ T├¡ch hß╗úp cß╗Öt last_interaction_at
    Γöé   Γö£ΓöÇΓöÇ routes.py                       ΓåÉ API Endpoints (th├¬m routes SCRUM-77)
    Γöé   ΓööΓöÇΓöÇ ...
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_periodic_customer_care.py  ΓåÉ Γÿà Test suite mß╗¢i cho SCRUM-77
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Thay ─æß╗òi DB

### Bß║úng mß╗¢i: `dbo.customer_interactions`
L╞░u to├án bß╗Ö lß╗ïch sß╗¡ t╞░╞íng t├íc ch─âm s├│c kh├ích h├áng:
- `id` (INT, PK, IDENTITY)
- `customer_id` (INT, FK ΓåÆ `dbo.customers.id`)
- `interaction_type` (NVARCHAR(50), default `'Gß╗ìi ─æiß╗çn ch─âm s├│c'`)
  - V├¡ dß╗Ñ: `'Gß╗ìi ─æiß╗çn ch─âm s├│c'` | `'Gß╗¡i email'` | `'Gß║╖p trß╗▒c tiß║┐p'` | `'─É├ính dß║Ñu ─æ├ú li├¬n hß╗ç ngay'`
- `notes` (NVARCHAR(MAX)) ΓÇö Ghi ch├║ nß╗Öi dung t╞░╞íng t├íc
- `created_by` (INT, FK ΓåÆ `dbo.users.id`)
- `created_at` (BIGINT, Unix ms)

### Cß╗Öt mß╗¢i trong `dbo.customers`:
- `last_interaction_at` (BIGINT) ΓÇö Unix timestamp (ms) cß╗ºa lß║ºn t╞░╞íng t├íc gß║ºn nhß║Ñt. Tß╗▒ ─æß╗Öng cß║¡p nhß║¡t mß╗ùi khi ghi nhß║¡n t╞░╞íng t├íc mß╗¢i.

---

## ≡ƒôí Chi tiß║┐t API Endpoints

### 1. Danh s├ích Ch─âm s├│c ─Éß╗ïnh kß╗│
- `GET /api/customers/periodic-care` ΓÇö Danh s├ích kh├ích h├áng cß║ºn ch─âm s├│c
  - Query params: `days` (default=30), `page`, `per_page`
  - Response: `{ items: [...days_without_interaction, contract_value, custom_fields...], total, days_threshold, page, per_page, total_pages }`

### 2. Lß╗ïch sß╗¡ & Ghi nhß║¡n T╞░╞íng t├íc
- `GET /api/customers/<id>/interactions` ΓÇö Lß╗ïch sß╗¡ t╞░╞íng t├íc cß╗ºa 1 kh├ích h├áng (mß╗¢i nhß║Ñt ΓåÆ c┼⌐ nhß║Ñt)
- `POST /api/customers/<id>/interactions` ΓÇö Ghi nhß║¡n t╞░╞íng t├íc mß╗¢i
  - Body: `{ "interaction_type": "Gß╗ìi ─æiß╗çn ch─âm s├│c", "notes": "..." }`
- `POST /api/customers/<id>/mark-contacted` ΓÇö ─É├ính dß║Ñu ─æ├ú li├¬n hß╗ç nhanh (1 click)
  - Body: `{ "notes": "..." }` (t├╣y chß╗ìn)

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_periodic_customer_care.py -v
```

Kß║┐t quß║ú kiß╗âm thß╗¡: **Tß║Ñt cß║ú tests passed (100%)**.
