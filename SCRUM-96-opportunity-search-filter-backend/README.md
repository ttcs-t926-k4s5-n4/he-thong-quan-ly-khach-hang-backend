# SCRUM-96: T├¼m kiß║┐m, Lß╗ìc & L╞░u bß╗Ö lß╗ìc C╞í hß╗Öi kinh doanh (Opportunity Search & Filter) ΓÇö Backend Python

## ≡ƒôî 1. Tß╗òng quan Feature

User Story: **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn t├¼m kiß║┐m c╞í hß╗Öi theo nhiß╗üu ─æiß╗üu kiß╗çn v├á l╞░u c├íc bß╗Ö lß╗ìc th╞░ß╗¥ng d├╣ng ─æß╗â nhanh ch├│ng t├¼m lß║íi nhß╗»ng th╞░╞íng vß╗Ñ cß║ºn th├║c ─æß║⌐y chß╗æt sale."**

Feature n├áy cung cß║Ñp c├┤ng cß╗Ñ t├¼m kiß║┐m v├á lß╗ìc c╞í hß╗Öi ─æa ti├¬u ch├¡ mß║ính mß║╜, ph├ón trang v├á sß║»p xß║┐p an to├án, ─æß╗ông thß╗¥i cho ph├⌐p ng╞░ß╗¥i d├╣ng l╞░u lß║íi c├íc bß╗Ö lß╗ìc t├╣y chß╗ënh c├í nh├ón (Saved Filters) ─æß╗â t├íi sß╗¡ dß╗Ñng vß╗¢i mß╗Öt thao t├íc.

---

## ≡ƒöÑ 2. C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng Backend

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. T├¼m kiß║┐m ─æa tr╞░ß╗¥ng** | `keyword` t├¼m ─æß╗ông thß╗¥i theo t├¬n c╞í hß╗Öi, m├ú c╞í hß╗Öi (ID) v├á t├¬n kh├ích h├áng li├¬n quan. |
| **2. Lß╗ìc ─æa ─æiß╗üu kiß╗çn** | Hß╗ù trß╗ú kß║┐t hß╗úp: `stage`, `min_value`, `max_value`, `close_date_from`, `close_date_to`, `product_id`, `owner_id`, v├á c├íc tr╞░ß╗¥ng t├╣y chß╗ënh (`cf_*`). |
| **3. Validation chß║╖t chß║╜** | Kiß╗âm tra `min_value <= max_value` v├á `close_date_from <= close_date_to` (trß║ú vß╗ü HTTP 400 nß║┐u vi phß║ím). |
| **4. Sß║»p xß║┐p an to├án (Whitelist)** | Chß╗ë cho ph├⌐p sß║»p xß║┐p theo c├íc tr╞░ß╗¥ng: `created_at`, `value`, `stage`, `expected_close_date`, `title`, `id`. Ng─ân chß║╖n SQL Injection qua `ORDER BY`. |
| **5. Ph├ón quyß╗ün dß╗» liß╗çu (RBAC Data Scope)** | Nh├ón vi├¬n kinh doanh (`employee`) tß╗▒ ─æß╗Öng ─æ╞░ß╗úc lß╗ìc chß╗ë thß║Ñy c╞í hß╗Öi do m├¼nh sß╗ƒ hß╗»u hoß║╖c ─æ╞░ß╗úc chia sß║╗ (SCRUM-97); Quß║ún l├╜ (`manager`) v├á Admin thß║Ñy to├án bß╗Ö. |
| **6. Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u (Saved Filters)** | Cung cß║Ñp ─æß║ºy ─æß╗º RESTful API (Tß║ío, Xem danh s├ích, Chi tiß║┐t, Sß╗¡a, X├│a). Kiß╗âm tra quyß╗ün sß╗ƒ hß╗»u bß╗Ö lß╗ìc (HTTP 403 nß║┐u truy cß║¡p cß╗ºa ng╞░ß╗¥i kh├íc). |
| **7. Bß║úo mß║¡t cß║Ñu h├¼nh** | Tß╗▒ ─æß╗Öng lß╗ìc bß╗Å c├íc th├┤ng tin nhß║íy cß║úm (token, password, secret) tr╞░ß╗¢c khi l╞░u v├áo `filter_config`. |

---

## ≡ƒôé 3. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-96-opportunity-search-filter-backend/
Γö£ΓöÇΓöÇ README.md                                    ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_96_opportunity_filters.sql        ΓåÉ Migration CSDL: bß║úng saved_opportunity_filters + cß╗Öt product_id
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ opportunity_filters.py               ΓåÉ Γÿà Module mß╗¢i: T├¼m kiß║┐m, lß╗ìc n├óng cao & CRUD Saved Filters
    Γöé   Γö£ΓöÇΓöÇ opportunities.py                     ΓåÉ Module C╞í hß╗Öi
    Γöé   Γö£ΓöÇΓöÇ routes.py                            ΓåÉ API Endpoints (GET /opportunities + /opportunity-filters)
    Γöé   ΓööΓöÇΓöÇ ...                                  ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_opportunity_filters.py         ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (13 test cases)
```

---

## ≡ƒùä∩╕Å 4. Database Schema & Migration

### Bß║úng mß╗¢i: `dbo.saved_opportunity_filters`
L╞░u trß╗» c├íc cß║Ñu h├¼nh bß╗Ö lß╗ìc ─æ╞░ß╗úc c├í nh├ón h├│a cho tß╗½ng ng╞░ß╗¥i d├╣ng:

| Cß╗Öt | Kiß╗âu dß╗» liß╗çu | R├áng buß╗Öc | M├┤ tß║ú |
|---|---|---|---|
| `id` | `INT` | `IDENTITY(1,1) PRIMARY KEY` | Kh├│a ch├¡nh tß╗▒ t─âng |
| `user_id` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id) ON DELETE CASCADE` | ID ng╞░ß╗¥i d├╣ng sß╗ƒ hß╗»u bß╗Ö lß╗ìc |
| `filter_name` | `NVARCHAR(255)` | `NOT NULL` | T├¬n bß╗Ö lß╗ìc do ng╞░ß╗¥i d├╣ng ─æß║╖t |
| `filter_config` | `NVARCHAR(MAX)` | `NOT NULL` | Chuß╗ùi JSON chß╗⌐a c├íc ti├¬u ch├¡ lß╗ìc ─æ├ú l╞░u |
| `created_at` | `BIGINT` | `NOT NULL` | Thß╗¥i ─æiß╗âm tß║ío (UTC epoch ms) |
| `updated_at` | `BIGINT` | `NOT NULL` | Thß╗¥i ─æiß╗âm cß║¡p nhß║¡t (UTC epoch ms) |

### Index tß╗æi ╞░u:
- `IX_saved_opp_filters_user_id` tr├¬n `(user_id, created_at DESC)`: Tß╗æi ╞░u tß║úi danh s├ích bß╗Ö lß╗ìc cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi.

### Cß╗Öt bß╗ò sung trong `dbo.opportunities`:
- `product_id INT NULL`: L╞░u trß╗» ID sß║ún phß║⌐m li├¬n quan ─æß║┐n c╞í hß╗Öi.

---

## ≡ƒôí 5. Chi tiß║┐t API Endpoints

### 1. `GET /api/opportunities` (T├¼m kiß║┐m & Lß╗ìc c╞í hß╗Öi)
- **Query Parameters**:
  - `keyword`: T├¼m theo t├¬n, m├ú c╞í hß╗Öi, t├¬n kh├ích h├áng
  - `stage`: Giai ─æoß║ín b├ín h├áng
  - `min_value`, `max_value`: Khoß║úng gi├í trß╗ï
  - `close_date_from`, `close_date_to`: Khoß║úng ng├áy chß╗æt dß╗▒ kiß║┐n
  - `product_id`: Lß╗ìc theo ID sß║ún phß║⌐m
  - `owner_id`: Lß╗ìc theo ID ng╞░ß╗¥i sß╗ƒ hß╗»u
  - `sort_by`: `created_at`, `value`, `stage`, `expected_close_date`, `title`, `id`
  - `sort_order`: `asc` hoß║╖c `desc` (mß║╖c ─æß╗ïnh: `desc`)
  - `page`: Sß╗æ trang (mß║╖c ─æß╗ïnh: `1`)
  - `page_size`: Sß╗æ bß║ún ghi mß╗ùi trang (mß║╖c ─æß╗ïnh: `20`, hß╗ù trß╗ú alias `per_page`)
- **Response**: Trß║ú vß╗ü `items`, `total`, `page`, `page_size`, `total_pages`, `sort_by`, `sort_order`.

### 2. Quß║ún l├╜ Bß╗Ö lß╗ìc ─æ├ú l╞░u (`/api/opportunity-filters`)
- `POST /api/opportunity-filters`: Tß║ío bß╗Ö lß╗ìc mß╗¢i
- `GET /api/opportunity-filters`: Lß║Ñy danh s├ích bß╗Ö lß╗ìc cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi
- `GET /api/opportunity-filters/<id>`: Lß║Ñy chi tiß║┐t bß╗Ö lß╗ìc
- `PUT /api/opportunity-filters/<id>`: Cß║¡p nhß║¡t bß╗Ö lß╗ìc
- `DELETE /api/opportunity-filters/<id>`: X├│a bß╗Ö lß╗ìc

---

## ≡ƒº¬ 6. H╞░ß╗¢ng dß║½n Chß║íy Kiß╗âm thß╗¡ (Testing)

```bash
cd backend
python -m unittest tests/test_opportunity_filters.py -v
```

Kß║┐t quß║ú: **13/13 tests passed (100% OK)**.
