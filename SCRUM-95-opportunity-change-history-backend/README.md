# SCRUM-95: Lß╗ïch sß╗¡ Thay ─æß╗òi C╞í hß╗Öi kinh doanh (Opportunity Change History) ΓÇö Backend Python

## ≡ƒôî 1. Tß╗òng quan Feature

User Story: **"L├á Tr╞░ß╗ƒng nh├│m kinh doanh, t├┤i muß╗æn xem lß╗ïch sß╗¡ thay ─æß╗òi cß╗ºa mß╗Öt c╞í hß╗Öi kinh doanh (bao gß╗ôm gi├í trß╗ï c┼⌐, gi├í trß╗ï mß╗¢i, ng╞░ß╗¥i thß╗▒c hiß╗çn v├á thß╗¥i ─æiß╗âm thay ─æß╗òi) ─æß╗â theo d├╡i diß╗àn biß║┐n ─æ├ám ph├ín v├á ─æ├ính gi├í hiß╗çu quß║ú l├ám viß╗çc cß╗ºa nh├ón vi├¬n."**

Feature n├áy cung cß║Ñp c╞í chß║┐ kiß╗âm to├ín (audit trail) nguy├¬n tß╗¡ cho c╞í hß╗Öi kinh doanh, tß╗▒ ─æß╗Öng theo d├╡i v├á l╞░u trß╗» d├ái hß║ín mß╗ìi thay ─æß╗òi tr├¬n c├íc tr╞░ß╗¥ng nghiß╗çp vß╗Ñ trß╗ìng yß║┐u:
- **Stage**: Giai ─æoß║ín b├ín h├áng trong pipeline
- **Value**: Gi├í trß╗ï c╞í hß╗Öi kinh doanh
- **Expected Close Date**: Ng├áy chß╗æt dß╗▒ kiß║┐n
- **Owner**: Ng╞░ß╗¥i sß╗ƒ hß╗»u c╞í hß╗Öi (`owner_id`)

---

## ≡ƒöÑ 2. C├íc Y├¬u cß║ºu Nghiß╗çp vß╗Ñ & Giß║úi ph├íp Backend

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Theo d├╡i 4 tr╞░ß╗¥ng trß╗ìng yß║┐u** | H├ám `compute_opportunity_diff()` tß╗▒ ─æß╗Öng so s├ính ch├¡nh x├íc `old_value` v├á `new_value` cß╗ºa: Stage, Value, Expected Close Date, Owner. |
| **2. Ghi nhß║¡n ─æß║ºy ─æß╗º khi cß║¡p nhß║¡t nhiß╗üu tr╞░ß╗¥ng** | Mß╗Öt request cß║¡p nhß║¡t c├│ thß╗â thay ─æß╗òi nhiß╗üu tr╞░ß╗¥ng; hß╗ç thß╗æng sß║╜ sinh ra ─æß║ºy ─æß╗º c├íc bß║ún ghi lß╗ïch sß╗¡ t╞░╞íng ß╗⌐ng cho mß╗ùi tr╞░ß╗¥ng ─æ├ú thay ─æß╗òi. |
| **3. Chß╗ë ghi khi gi├í trß╗ï thß╗▒c sß╗▒ thay ─æß╗òi** | Bß╗Å qua c├íc tr╞░ß╗¥ng kh├┤ng thay ─æß╗òi (giß╗» nguy├¬n gi├í trß╗ï c┼⌐). Kh├┤ng ghi bß║ún ghi r├íc v├áo CSDL. |
| **4. Ghi lß╗ïch sß╗¡ c├╣ng transaction (Atomicity)** | Cß║¡p nhß║¡t c╞í hß╗Öi v├á ch├¿n lß╗ïch sß╗¡ diß╗àn ra trong c├╣ng mß╗Öt transaction CSDL. Nß║┐u c├│ lß╗ùi xß║úy ra, to├án bß╗Ö sß║╜ `ROLLBACK` lß║¡p tß╗⌐c, kh├┤ng ─æß╗â lß║íi dß╗» liß╗çu kh├┤ng nhß║Ñt qu├ín hoß║╖c lß╗ïch sß╗¡ giß║ú. |
| **5. Kh├┤ng cho Client giß║ú mß║ío ng╞░ß╗¥i thß╗▒c hiß╗çn** | `changed_by` lu├┤n ─æ╞░ß╗úc tr├¡ch xuß║Ñt tß╗½ phi├¬n x├íc thß╗▒c an to├án ph├¡a Backend (`user.id`), loß║íi bß╗Å ho├án to├án c├íc tr╞░ß╗¥ng `user_id` do Client tß╗▒ gß╗¡i. |
| **6. Bß║Ñt biß║┐n (Immutable Audit Trail)** | Lß╗ïch sß╗¡ chß╗ë ─æ╞░ß╗úc truy xuß║Ñt qua `GET /api/opportunities/<id>/history`. Kh├┤ng cung cß║Ñp API th├¬m/sß╗¡a/x├│a lß╗ïch sß╗¡ cho Client. |
| **7. Ph├ón quyß╗ün chß║╖t chß║╜** | Admin v├á Tr╞░ß╗ƒng nh├│m (Manager) c├│ quyß╗ün xem lß╗ïch sß╗¡ cß╗ºa mß╗ìi c╞í hß╗Öi; Nh├ón vi├¬n kinh doanh (Employee) chß╗ë ─æ╞░ß╗úc xem lß╗ïch sß╗¡ c╞í hß╗Öi do ch├¡nh m├¼nh sß╗ƒ hß╗»u hoß║╖c tß║ío ra. Ng─ân chß║╖n triß╗çt ─æß╗â truy cß║¡p tr├íi ph├⌐p (HTTP 403). |

---

## ≡ƒôé 3. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-95-opportunity-change-history-backend/
Γö£ΓöÇΓöÇ README.md                                   ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_95_opportunity_history.sql        ΓåÉ Migration CSDL: bß║úng opportunity_history + cß╗Öt owner_id
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ opportunity_history.py              ΓåÉ Γÿà Module mß╗¢i: L├╡i quß║ún l├╜ & truy vß║Ñn lß╗ïch sß╗¡ thay ─æß╗òi c╞í hß╗Öi
    Γöé   Γö£ΓöÇΓöÇ opportunities.py                    ΓåÉ Module C╞í hß╗Öi (t├¡ch hß╗úp diff & ghi lß╗ïch sß╗¡ nguy├¬n tß╗¡)
    Γöé   Γö£ΓöÇΓöÇ routes.py                           ΓåÉ API Endpoints (GET history + PUT update opportunity)
    Γöé   ΓööΓöÇΓöÇ ...                                 ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_opportunity_history.py         ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (21 test cases)
```

---

## ≡ƒùä∩╕Å 4. Database Schema & Migration

### Bß║úng mß╗¢i: `dbo.opportunity_history`
L╞░u trß╗» to├án bß╗Ö c├íc thay ─æß╗òi cß╗ºa c╞í hß╗Öi theo thß╗¥i gian (sß╗¡ dß╗Ñng epoch milliseconds UTC nhß║Ñt qu├ín):

| Cß╗Öt | Kiß╗âu dß╗» liß╗çu | R├áng buß╗Öc | M├┤ tß║ú |
|---|---|---|---|
| `id` | `BIGINT` | `IDENTITY(1,1) PRIMARY KEY` | Kh├│a ch├¡nh tß╗▒ t─âng |
| `opportunity_id` | `INT` | `FOREIGN KEY REFERENCES dbo.opportunities(id) ON DELETE CASCADE` | ID c╞í hß╗Öi kinh doanh |
| `field_name` | `NVARCHAR(100)` | `NOT NULL` | T├¬n tr╞░ß╗¥ng (`stage`, `value`, `expected_close_date`, `owner`) |
| `old_value` | `NVARCHAR(MAX)` | `NULL` | Gi├í trß╗ï tr╞░ß╗¢c khi thay ─æß╗òi |
| `new_value` | `NVARCHAR(MAX)` | `NULL` | Gi├í trß╗ï sau khi thay ─æß╗òi |
| `changed_by` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID ng╞░ß╗¥i thß╗▒c hiß╗çn thay ─æß╗òi |
| `changed_at` | `BIGINT` | `NOT NULL` | Thß╗¥i ─æiß╗âm thay ─æß╗òi (UTC epoch ms) |

### Indexes tß╗æi ╞░u hiß╗çu n─âng:
- `IX_opp_hist_opp_id_changed_at` tr├¬n `(opportunity_id, changed_at DESC)`: Tß╗æi ╞░u truy vß║Ñn ph├ón trang theo c╞í hß╗Öi.
- `IX_opp_hist_field_name` tr├¬n `(opportunity_id, field_name)`: Tß╗æi ╞░u lß╗ìc lß╗ïch sß╗¡ theo tr╞░ß╗¥ng cß╗Ñ thß╗â.

### Bß╗ò sung cß╗Öt v├áo `dbo.opportunities`:
- `owner_id INT NULL`: L╞░u trß╗» ng╞░ß╗¥i sß╗ƒ hß╗»u c╞í hß╗Öi (mß║╖c ─æß╗ïnh nhß║¡n gi├í trß╗ï tß╗½ `created_by` nß║┐u ch╞░a g├ín).

---

## ≡ƒôí 5. Chi tiß║┐t API Endpoints

### 1. `GET /api/opportunities/<opportunity_id>/history`
Lß║Ñy lß╗ïch sß╗¡ thay ─æß╗òi cß╗ºa mß╗Öt c╞í hß╗Öi kinh doanh.

#### Query Parameters:
| Tham sß╗æ | Kiß╗âu | Mß║╖c ─æß╗ïnh | M├┤ tß║ú |
|---|---|---|---|
| `page` | `int` | `1` | Sß╗æ trang cß║ºn lß║Ñy (tß╗½ 1) |
| `page_size` | `int` | `20` | Sß╗æ bß║ún ghi mß╗ùi trang (hß╗ù trß╗ú cß║ú alias `per_page`) |
| `field` | `string` | `""` | Lß╗ìc theo t├¬n tr╞░ß╗¥ng thay ─æß╗òi (`stage`, `value`, `expected_close_date`, `owner`) |

#### Ph├ón quyß╗ün:
- `admin`, `manager`: To├án quyß╗ün xem mß╗ìi c╞í hß╗Öi.
- `employee`: Chß╗ë xem c╞í hß╗Öi do m├¼nh sß╗ƒ hß╗»u (`owner_id` hoß║╖c `created_by`).

#### Response Success (HTTP 200):
```json
{
  "items": [
    {
      "id": 15,
      "opportunity_id": 1,
      "field_name": "stage",
      "field_label": "Giai ─æoß║ín",
      "old_value": "Mß╗¢i tß║ío",
      "new_value": "─É├ám ph├ín",
      "changed_by": 2,
      "changed_by_name": "Trß║ºn Thß╗ï B",
      "changed_by_email": "manager@company.vn",
      "changed_at": 1729158000000,
      "changed_at_iso": "2026-10-17T09:40:00Z"
    },
    {
      "id": 16,
      "opportunity_id": 1,
      "field_name": "value",
      "field_label": "Gi├í trß╗ï c╞í hß╗Öi",
      "old_value": "50000000",
      "new_value": "80000000",
      "changed_by": 2,
      "changed_by_name": "Trß║ºn Thß╗ï B",
      "changed_by_email": "manager@company.vn",
      "changed_at": 1729158000000,
      "changed_at_iso": "2026-10-17T09:40:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2,
  "total_pages": 1
}
```

#### Response Errors:
- `401 Unauthorized`: Ch╞░a ─æ─âng nhß║¡p hoß║╖c session ─æ├ú hß║┐t hß║ín.
- `403 Forbidden`: Ng╞░ß╗¥i d├╣ng kh├┤ng c├│ quyß╗ün truy cß║¡p c╞í hß╗Öi n├áy.
- `404 Not Found`: Kh├┤ng t├¼m thß║Ñy c╞í hß╗Öi kinh doanh.

---

### 2. `PUT /api/opportunities/<opportunity_id>` (T├¡ch hß╗úp tß╗▒ ─æß╗Öng ghi lß╗ïch sß╗¡)
Cß║¡p nhß║¡t c╞í hß╗Öi kinh doanh. Backend tß╗▒ ─æß╗Öng so s├ính dß╗» liß╗çu tr╞░ß╗¢c v├á sau cß║¡p nhß║¡t, sau ─æ├│ ghi c├íc thay ─æß╗òi v├áo `dbo.opportunity_history` trong c├╣ng mß╗Öt transaction.

#### Request Body (JSON):
```json
{
  "title": "Hß╗úp ─æß╗ông phß║ºn mß╗üm ERP",
  "customer_id": 10,
  "value": 150000000,
  "stage": "─É├ám ph├ín",
  "expected_close_date": "2026-12-31",
  "owner_id": 5
}
```

#### Quy tß║»c xß╗¡ l├╜:
- Tß╗▒ ─æß╗Öng ph├ít hiß╗çn thay ─æß╗òi tr├¬n `stage`, `value`, `expected_close_date`, `owner`.
- `changed_by` ─æ╞░ß╗úc g├ín bß║▒ng `user.id` tß╗½ session ─æ├ú ─æ─âng nhß║¡p.
- Nß║┐u kh├┤ng c├│ tr╞░ß╗¥ng n├áo thay ─æß╗òi, kh├┤ng tß║ío bß║ún ghi lß╗ïch sß╗¡ giß║ú.
- Nß║┐u cß║¡p nhß║¡t CSDL lß╗ùi, to├án bß╗Ö thao t├íc update v├á lß╗ïch sß╗¡ ─æ╞░ß╗úc rollback ngay lß║¡p tß╗⌐c.

---

## ≡ƒº¬ 6. H╞░ß╗¢ng dß║½n Chß║íy Migration & Kiß╗âm thß╗¡ (Testing)

### 1. Chß║íy Migration SQL Server:
```sql
-- Chß║íy file script trong Sql Server Management Studio hoß║╖c sqlcmd:
sqlcmd -S localhost -d crm_db -U sa -P YourPassword -i database/scrum_95_opportunity_history.sql
```
*L╞░u ├╜: Hß╗ç thß╗æng c┼⌐ng t├¡ch hß╗úp c╞í chß║┐ tß╗▒ ─æß╗Öng khß╗ƒi tß║ío bß║úng (`ensure_opportunity_history_table`) ngay khi chß║íy ß╗⌐ng dß╗Ñng.*

### 2. Chß║íy Automated Tests:
```bash
cd backend
python -m unittest tests/test_opportunity_history.py -v
```

Kß║┐t quß║ú kiß╗âm thß╗¡ thß╗▒c tß║┐:
```
test_update_opportunity_commits_both_opp_and_history ... ok
test_admin_can_access_any_opportunity ... ok
test_employee_can_access_own_opportunity ... ok
test_employee_cannot_access_other_opportunity ... ok
test_manager_can_access_any_opportunity ... ok
test_diff_expected_close_date_changed ... ok
test_diff_multiple_fields_changed ... ok
test_diff_owner_changed ... ok
test_diff_stage_changed ... ok
test_diff_value_changed ... ok
test_no_diff_when_data_unchanged ... ok
test_get_history_empty ... ok
test_get_history_with_field_filter ... ok
test_employee_can_access_own_opportunity_history ... ok
test_history_endpoint_forbidden_for_other_employee_returns_403 ... ok
test_history_endpoint_opportunity_not_found_returns_404 ... ok
test_history_endpoint_success_for_manager ... ok
test_history_endpoint_unauthenticated_returns_401 ... ok
test_update_opportunity_owner_not_found_returns_404 ... ok
test_update_opportunity_tracks_changed_by_from_session ... ok
test_rollback_on_update_failure ... ok

----------------------------------------------------------------------
Ran 21 tests in 0.449s

OK
```
