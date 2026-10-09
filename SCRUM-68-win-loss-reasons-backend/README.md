# S2-10: Khai b├ío Danh mß╗Ñc L├╜ do Thß║»ng/Thua & ─Éß╗æi thß╗º cß║ính tranh (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy phß╗Ñc vß╗Ñ nhu cß║ºu cß╗ºa **Gi├ím ─æß╗æc kinh doanh (Sales Manager)** nhß║▒m chuß║⌐n h├│a dß╗» liß╗çu ─æ├│ng c╞í hß╗Öi (Sales Closure Intelligence):
1. Khai b├ío danh mß╗Ñc **L├╜ do Thß║»ng (`win_reasons`)** v├á **L├╜ do Thua (`loss_reasons`)** ri├¬ng biß╗çt.
2. Khai b├ío danh mß╗Ñc **─Éß╗æi thß╗º cß║ính tranh (`competitors`)**.
3. ├üp dß╗Ñng quy tß║»c r├áng buß╗Öc bß║»t buß╗Öc khi chß╗æt c╞í hß╗Öi:
   - Khi chß╗æt c╞í hß╗Öi th├ánh c├┤ng (`closed_won`): Bß║»t buß╗Öc phß║úi nhß║¡p **L├╜ do Thß║»ng**.
   - Khi chß╗æt c╞í hß╗Öi thß║Ñt bß║íi (`closed_lost`): Bß║»t buß╗Öc phß║úi nhß║¡p **L├╜ do Thua** v├á chß╗ìn **─Éß╗æi thß╗º cß║ính tranh** chiß║┐n thß║»ng.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & Giß║úi ph├íp ─É├íp ß╗⌐ng

| Y├¬u cß║ºu Story | Giß║úi ph├íp Backend |
|---|---|
| **1. Khai b├ío danh mß╗Ñc L├╜ do Thß║»ng / Thua ri├¬ng biß╗çt** | Bß║úng `dbo.win_loss_reasons` l╞░u c├íc l├╜ do vß╗¢i `reason_type = 'win'` hoß║╖c `'loss'`, `reason_code`, `reason_title`. |
| **2. Danh mß╗Ñc ─Éß╗æi thß╗º cß║ính tranh** | Bß║úng `dbo.competitors` l╞░u t├¬n ─æß╗æi thß╗º, website, ─æiß╗âm mß║ính, ─æiß╗âm yß║┐u. |
| **3. R├áng buß╗Öc dß╗» liß╗çu bß║»t buß╗Öc khi ─æ├│ng c╞í hß╗Öi** | H├ám `validate_opportunity_closure` kiß╗âm tra khi cß║¡p nhß║¡t giai ─æoß║ín c╞í hß╗Öi: Won bß║»t buß╗Öc c├│ `win_reason_id`, Lost bß║»t buß╗Öc c├│ `loss_reason_id` v├á `competitor_id`. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
S2-10-win-loss-reasons-backend/
Γö£ΓöÇΓöÇ README.md                           ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ s2_10_win_loss_reasons.sql      ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ win_loss_reasons.py         ΓåÉ Module quß║ún l├╜ l├╜ do thß║»ng/thua & ─æß╗æi thß╗º cß║ính tranh
    Γöé   Γö£ΓöÇΓöÇ opportunities.py            ΓåÉ T├¡ch hß╗úp validation ─æ├│ng c╞í hß╗Öi kinh doanh
    Γöé   Γö£ΓöÇΓöÇ routes.py                   ΓåÉ API Endpoints
    Γöé   ΓööΓöÇΓöÇ ...
    ΓööΓöÇΓöÇ tests/
        ΓööΓöÇΓöÇ test_win_loss_reasons.py    ΓåÉ Automated integration tests
```

---

## ≡ƒôí Chi tiß║┐t API Endpoints

### 1. L├╜ do Thß║»ng / Thua
- `GET /api/win-loss-reasons?type=win|loss` ΓÇö Danh s├ích l├╜ do thß║»ng/thua
- `POST /api/win-loss-reasons` ΓÇö Khai b├ío l├╜ do mß╗¢i (Sales Manager / Admin)
- `PUT /api/win-loss-reasons/<id>` ΓÇö Cß║¡p nhß║¡t l├╜ do (Sales Manager / Admin)
- `DELETE /api/win-loss-reasons/<id>` ΓÇö X├│a l├╜ do (Sales Manager / Admin)

### 2. ─Éß╗æi thß╗º Cß║ính tranh
- `GET /api/competitors` ΓÇö Danh s├ích ─æß╗æi thß╗º cß║ính tranh
- `POST /api/competitors` ΓÇö Khai b├ío ─æß╗æi thß╗º mß╗¢i (Sales Manager / Admin)
- `GET /api/competitors/<id>` ΓÇö Xem chi tiß║┐t ─æß╗æi thß╗º
- `PUT /api/competitors/<id>` ΓÇö Cß║¡p nhß║¡t ─æß╗æi thß╗º (Sales Manager / Admin)
- `DELETE /api/competitors/<id>` ΓÇö X├│a ─æß╗æi thß╗º (Sales Manager / Admin)
