# SCRUM-75: Bß╗Ö lß╗ìc n├óng cao & Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u cho Kh├ích h├áng (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy cung cß║Ñp t├¡nh n─âng cho **Nh├ón vi├¬n kinh doanh & Ch─âm s├│c kh├ích h├áng** thß╗▒c hiß╗çn t├¼m kiß║┐m v├á lß╗ìc n├óng cao tr├¬n to├án bß╗Ö danh s├ích Kh├ích h├áng theo nhiß╗üu ti├¬u ch├¡ kß║┐t hß╗úp, ─æß╗ông thß╗¥i cho ph├⌐p l╞░u lß║íi bß╗Ö lß╗ìc th╞░ß╗¥ng d├╣ng ─æß╗â t├íi sß╗¡ dß╗Ñng nhanh ch├│ng.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. T├¼m kiß║┐m ─æa tr╞░ß╗¥ng** | API hß╗ù trß╗ú tham sß╗æ `q` t├¼m ─æß╗ông thß╗¥i trong: T├¬n kh├ích h├áng, Sß╗æ ─æiß╗çn thoß║íi, Email, ─Éß╗ïa chß╗ë v├á cß║ú M├ú sß╗æ thuß║┐ (tr╞░ß╗¥ng t├╣y chß╗ënh `tax_code`). |
| **2. Lß╗ìc theo Trß║íng th├íi** | Tham sß╗æ `status` lß╗ìc theo trß║íng th├íi kh├ích h├áng (Tiß╗üm n─âng, ─Éang hß╗úp t├íc, Kh├┤ng hß╗úp t├íc, v.v.). |
| **3. Lß╗ìc theo Ng├ánh nghß╗ü / Quy m├┤ / Khu vß╗▒c** | Tham sß╗æ `industry`, `scale`, `region` lß╗ìc qua c├íc tr╞░ß╗¥ng t├╣y chß╗ënh (custom fields) linh hoß║ít. |
| **4. Lß╗ìc theo Ng╞░ß╗¥i sß╗ƒ hß╗»u (Owner)** | Tham sß╗æ `owner_id` lß╗ìc kh├ích h├áng theo nh├ón vi├¬n phß╗Ñ tr├ích. |
| **5. Ph├ón trang & Sß║»p xß║┐p** | Tham sß╗æ `page`, `per_page`, `sort_by`, `order` kiß╗âm so├ít ph├ón trang v├á thß╗⌐ tß╗▒ kß║┐t quß║ú. |
| **6. Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u (Saved Filters CRUD)** | API ─æß║ºy ─æß╗º cho Tß║ío / ─Éß╗ìc / Cß║¡p nhß║¡t / X├│a bß╗Ö lß╗ìc ─æ├ú l╞░u theo tß╗½ng ng╞░ß╗¥i d├╣ng, l╞░u v├áo bß║úng `dbo.saved_filters`. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-75-customer-filter-backend/
Γö£ΓöÇΓöÇ README.md                               ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_75_customer_filter.sql        ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ customer_filters.py             ΓåÉ Γÿà Module mß╗¢i: Bß╗Ö lß╗ìc ─æa ti├¬u ch├¡ & Saved Filters
    Γöé   Γö£ΓöÇΓöÇ custom_fields.py                ΓåÉ T├¡ch hß╗úp lß╗ìc theo custom fields
    Γöé   Γö£ΓöÇΓöÇ customers.py                    ΓåÉ Quß║ún l├╜ Kh├ích h├áng
    Γöé   Γö£ΓöÇΓöÇ routes.py                       ΓåÉ API Endpoints (th├¬m routes SCRUM-75)
    Γöé   ΓööΓöÇΓöÇ ...
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_customer_filter.py         ΓåÉ Γÿà Test suite mß╗¢i cho SCRUM-75
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Bß║úng mß╗¢i

### `dbo.saved_filters`
L╞░u trß╗» bß╗Ö lß╗ìc ─æ├ú ─æ╞░ß╗úc ng╞░ß╗¥i d├╣ng ─æß║╖t t├¬n v├á l╞░u lß║íi:
- `id` (INT, PK, IDENTITY)
- `user_id` (INT, FK ΓåÆ `dbo.users.id`) ΓÇö Ng╞░ß╗¥i tß║ío bß╗Ö lß╗ìc
- `name` (NVARCHAR(255)) ΓÇö T├¬n bß╗Ö lß╗ìc do ng╞░ß╗¥i d├╣ng ─æß║╖t
- `filter_target` (VARCHAR(50), default `'customer'`) ΓÇö Loß║íi ─æß╗æi t╞░ß╗úng lß╗ìc
- `criteria_json` (NVARCHAR(MAX)) ΓÇö JSON chß╗⌐a c├íc ti├¬u ch├¡ lß╗ìc ─æ├ú l╞░u
- `created_at` / `updated_at` (BIGINT, Unix timestamp ms)

---

## ≡ƒôí Chi tiß║┐t API Endpoints

### 1. T├¼m kiß║┐m & Lß╗ìc Kh├ích h├áng
- `GET /api/customers/search-filter` ΓÇö T├¼m kiß║┐m v├á lß╗ìc ─æa ti├¬u ch├¡
  - Query params: `q`, `status`, `industry`, `scale`, `region`, `owner_id`, `page`, `per_page`, `sort_by`, `order`, `cf_<key>=value`
  - Response: `{ items: [...], total, page, per_page, total_pages }`

### 2. Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u (Saved Filters)
- `GET /api/saved-filters?target=customer` ΓÇö Danh s├ích bß╗Ö lß╗ìc cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi
- `POST /api/saved-filters` ΓÇö L╞░u bß╗Ö lß╗ìc mß╗¢i
  - Body: `{ "name": "T├¬n bß╗Ö lß╗ìc", "criteria": {...}, "filter_target": "customer" }`
- `GET /api/saved-filters/<id>` ΓÇö Chi tiß║┐t 1 bß╗Ö lß╗ìc ─æ├ú l╞░u
- `PUT /api/saved-filters/<id>` ΓÇö Cß║¡p nhß║¡t bß╗Ö lß╗ìc ─æ├ú l╞░u
- `DELETE /api/saved-filters/<id>` ΓÇö X├│a bß╗Ö lß╗ìc ─æ├ú l╞░u

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_customer_filter.py -v
```

Kß║┐t quß║ú kiß╗âm thß╗¡: **Tß║Ñt cß║ú tests passed (100%)**.
