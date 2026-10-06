# SCRUM-17 / SCRUM-66: Khai b├ío tr╞░ß╗¥ng t├╣y chß╗ënh cho Kh├ích h├áng & C╞í hß╗Öi (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy cung cß║Ñp t├¡nh n─âng cho ph├⌐p **Quß║ún trß╗ï hß╗ç thß╗æng (System Admin)** ─æß╗ïnh ngh─⌐a c├íc **tr╞░ß╗¥ng t├╣y chß╗ënh (Custom Fields)** ─æß╗Öng cho 2 ─æß╗æi t╞░ß╗úng kinh doanh ch├¡nh:
1. **Kh├ích h├áng (`customer`)**
2. **C╞í hß╗Öi kinh doanh (`opportunity`)**

Nhß╗¥ ─æ├│, nh├ón vi├¬n c├│ thß╗â ─æ╞░a c├íc th├┤ng tin/cß╗Öt dß╗» liß╗çu ─æang theo d├╡i ngo├ái Excel v├áo hß╗ç thß╗æng mß╗Öt c├ích linh hoß║ít, ─æß╗ông bß╗Ö v├á c├│ kiß╗âm so├ít dß╗» liß╗çu.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Khai b├ío kiß╗âu dß╗» liß╗çu** | Hß╗ù trß╗ú 4 kiß╗âu: `text` (v─ân bß║ún), `number` (sß╗æ), `date` (ng├áy YYYY-MM-DD), `select` (danh s├ích chß╗ìn k├¿m c├íc t├╣y chß╗ìn options dß║íng JSON). |
| **2. Bß║»t buß╗Öc hay kh├┤ng (`is_required`)** | Cß║Ñu h├¼nh cß╗¥ `is_required` (True/False). Khi l╞░u th├┤ng tin Kh├ích h├áng/C╞í hß╗Öi, hß╗ç thß╗æng tß╗▒ ─æß╗Öng kiß╗âm tra v├á trß║ú vß╗ü phß║ún hß╗ôi lß╗ùi chi tiß║┐t nß║┐u thiß║┐u dß╗» liß╗çu bß║»t buß╗Öc. |
| **3. Hiß╗ân thß╗ï trong Biß╗âu mß║½u (Form Schema)** | API `/api/custom-fields/schema/<entity_type>` cung cß║Ñp cß║Ñu h├¼nh tr╞░ß╗¥ng ─æß╗Öng cho Frontend tß╗▒ ─æß╗Öng render form nhß║¡p liß╗çu k├¿m validate. |
| **4. Hiß╗ân thß╗ï trong Bß╗Ö lß╗ìc (Filter Engine)** | C├íc API danh s├ích `/api/customers` v├á `/api/opportunities` hß╗ù trß╗ú lß╗ìc ─æß╗Öng theo tr╞░ß╗¥ng t├╣y chß╗ënh qua query parameters `cf_<field_key>=value`. |
| **5. Xuß║Ñt bß║ún Excel (Excel Export Engine)** | C├íc API `/api/customers/export-excel` v├á `/api/opportunities/export-excel` tß║ío file Excel (`.xlsx`) chuy├¬n nghiß╗çp vß╗¢i ti├¬u ─æß╗ü ─æß╗Öng chß╗⌐a tß║Ñt cß║ú c├íc tr╞░ß╗¥ng t├╣y chß╗ënh ─æang k├¡ch hoß║ít. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-66-custom-fields-backend/
Γö£ΓöÇΓöÇ README.md                           ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_66_custom_fields.sql      ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ __init__.py                 ΓåÉ Application factory & CORS configuration
    Γöé   Γö£ΓöÇΓöÇ auth.py                     ΓåÉ Authentication & Session Management
    Γöé   Γö£ΓöÇΓöÇ custom_fields.py            ΓåÉ Module ─æß╗ïnh ngh─⌐a, validate & l╞░u trß╗» tr╞░ß╗¥ng t├╣y chß╗ënh
    Γöé   Γö£ΓöÇΓöÇ customers.py                ΓåÉ Quß║ún l├╜ Kh├ích h├áng t├¡ch hß╗úp tr╞░ß╗¥ng t├╣y chß╗ënh
    Γöé   Γö£ΓöÇΓöÇ db.py                       ΓåÉ Kß║┐t nß╗æi PyODBC vß╗¢i SQL Server
    Γöé   Γö£ΓöÇΓöÇ excel_export.py             ΓåÉ Exporter tß║ío file Excel (.xlsx) ─æß╗Öng
    Γöé   Γö£ΓöÇΓöÇ opportunities.py            ΓåÉ Quß║ún l├╜ C╞í hß╗Öi kinh doanh t├¡ch hß╗úp tr╞░ß╗¥ng t├╣y chß╗ënh
    Γöé   ΓööΓöÇΓöÇ routes.py                   ΓåÉ API Endpoints
    Γö£ΓöÇΓöÇ tests/
    Γöé   Γö£ΓöÇΓöÇ conftest.py
    Γöé   ΓööΓöÇΓöÇ test_custom_fields.py       ΓåÉ Automated integration test suite
    Γö£ΓöÇΓöÇ requirements.txt                ΓåÉ Python dependencies (Flask, pyodbc, openpyxl, pytest)
    Γö£ΓöÇΓöÇ run.py                          ΓåÉ Script khß╗ƒi chß║íy Flask backend
    ΓööΓöÇΓöÇ seed_data.py                    ΓåÉ Seed dß╗» liß╗çu mß║½u (User, Custom Fields, Customers, Opportunities)
```

---

## ≡ƒùä∩╕Å Database Schema

### 1. `dbo.custom_field_definitions`
L╞░u ─æß╗ïnh ngh─⌐a c├íc tr╞░ß╗¥ng t├╣y chß╗ënh do Admin tß║ío:
- `id` (INT, PK)
- `entity_type` (NVARCHAR(50), 'customer' | 'opportunity')
- `field_key` (NVARCHAR(100), Unique key per entity)
- `field_label` (NVARCHAR(200), Nh├ún hiß╗ân thß╗ï)
- `field_type` (NVARCHAR(50), 'text' | 'number' | 'date' | 'select')
- `options` (NVARCHAR(MAX), JSON array cho kiß╗âu 'select')
- `is_required` (BIT, Bß║»t buß╗Öc hay kh├┤ng)
- `description` (NVARCHAR(500))
- `display_order` (INT)
- `is_active` (BIT)

### 2. `dbo.custom_field_values`
L╞░u gi├í trß╗ï cß╗ºa tr╞░ß╗¥ng t├╣y chß╗ënh cho tß╗½ng bß║ún ghi:
- `id` (BIGINT, PK)
- `entity_type` (NVARCHAR(50))
- `entity_id` (INT, Customer ID hoß║╖c Opportunity ID)
- `field_id` (INT, FK tß╗¢i `custom_field_definitions.id`)
- `field_value` (NVARCHAR(MAX))

---

## ≡ƒôí Chi tiß║┐t API Endpoints

### 1. ─Éß╗ïnh ngh─⌐a Tr╞░ß╗¥ng T├╣y chß╗ënh (Admin Only)
- `GET /api/custom-fields?entity_type=customer|opportunity` ΓÇö Danh s├ích c├íc tr╞░ß╗¥ng t├╣y chß╗ënh
- `GET /api/custom-fields/schema/<entity_type>` ΓÇö Form schema render tß╗▒ ─æß╗Öng cho Frontend
- `POST /api/custom-fields` ΓÇö Tß║ío tr╞░ß╗¥ng t├╣y chß╗ënh mß╗¢i (Admin)
- `GET /api/custom-fields/<id>` ΓÇö Chi tiß║┐t 1 tr╞░ß╗¥ng
- `PUT /api/custom-fields/<id>` ΓÇö Cß║¡p nhß║¡t tr╞░ß╗¥ng t├╣y chß╗ënh (Admin)
- `DELETE /api/custom-fields/<id>` ΓÇö X├│a tr╞░ß╗¥ng t├╣y chß╗ënh (Admin)

### 2. Quß║ún l├╜ Kh├ích h├áng & C╞í hß╗Öi kinh doanh
- `GET /api/customers?q=search&status=Mß╗¢i&cf_industry=C├┤ng+nghß╗ç` ΓÇö Danh s├ích & Lß╗ìc theo tr╞░ß╗¥ng t├╣y chß╗ënh
- `POST /api/customers` ΓÇö Tß║ío kh├ích h├áng mß╗¢i k├¿m object `custom_fields: {"industry": "C├┤ng nghß╗ç"}`
- `PUT /api/customers/<id>` ΓÇö Cß║¡p nhß║¡t kh├ích h├áng & tr╞░ß╗¥ng t├╣y chß╗ënh
- `DELETE /api/customers/<id>` ΓÇö X├│a kh├ích h├áng
- `GET /api/customers/export-excel` ΓÇö Tß║úi file Excel (`.xlsx`) danh s├ích Kh├ích h├áng c├│ ─æß║ºy ─æß╗º cß╗Öt t├╣y chß╗ënh
- `GET /api/opportunities?q=search&stage=─É├ám+ph├ín&cf_lead_source=Website` ΓÇö Danh s├ích & Lß╗ìc C╞í hß╗Öi
- `POST /api/opportunities` ΓÇö Tß║ío c╞í hß╗Öi kinh doanh k├¿m tr╞░ß╗¥ng t├╣y chß╗ënh
- `PUT /api/opportunities/<id>` ΓÇö Cß║¡p nhß║¡t c╞í hß╗Öi
- `DELETE /api/opportunities/<id>` ΓÇö X├│a c╞í hß╗Öi
- `GET /api/opportunities/export-excel` ΓÇö Tß║úi file Excel (`.xlsx`) danh s├ích C╞í hß╗Öi c├│ ─æß║ºy ─æß╗º cß╗Öt t├╣y chß╗ënh

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng (Automated Testing)

Chß║íy bß╗Ö test t├¡ch hß╗úp vß╗¢i command:
```powershell
cd backend
.venv\Scripts\pytest tests/test_custom_fields.py
```
Kß║┐t quß║ú kiß╗âm thß╗¡: **9/9 tests passed (100%)**.
