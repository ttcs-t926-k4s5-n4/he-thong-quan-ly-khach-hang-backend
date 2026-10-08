# S2-09: Cß║Ñu h├¼nh c├íc giai ─æoß║ín Pipeline & X├íc suß║Ñt thß║»ng (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy phß╗Ñc vß╗Ñ nhu cß║ºu cß╗ºa **Gi├ím ─æß╗æc kinh doanh (Sales Manager)** ─æß╗â cß║Ñu h├¼nh quy tr├¼nh b├ín h├áng chuß║⌐n (Sales Pipeline), thiß║┐t lß║¡p x├íc suß║Ñt thß║»ng mß║╖c ─æß╗ïnh cho tß╗½ng giai ─æoß║ín v├á ─æß╗ïnh ngh─⌐a c├íc ─æiß╗üu kiß╗çn bß║»t buß╗Öc khi chuyß╗ân giai ─æoß║ín, gi├║p t├¡nh to├ín con sß╗æ dß╗▒ b├ío doanh sß╗æ (`forecast_amount`) ch├¡nh x├íc v├á c├│ c╞í sß╗ƒ khoa hß╗ìc.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & Giß║úi ph├íp ─É├íp ß╗⌐ng

| Y├¬u cß║ºu Story | Giß║úi ph├íp Backend |
|---|---|
| **1. Khai b├ío chuß╗ùi giai ─æoß║ín** | Quß║ún l├╜ c├íc giai ─æoß║ín (VD: Tiß║┐p cß║¡n [10%] ΓåÆ X├íc ─æß╗ïnh nhu cß║ºu [25%] ΓåÆ ─Éß╗ü xuß║Ñt giß║úi ph├íp [50%] ΓåÆ B├ío gi├í [70%] ΓåÆ ─É├ám ph├ín [85%] ΓåÆ Won [100%] / Lost [0%]). |
| **2. X├íc suß║Ñt thß║»ng mß║╖c ─æß╗ïnh & Dß╗▒ b├ío** | Mß╗ùi giai ─æoß║ín l╞░u `win_probability` (0 - 100%). API `/api/forecast/summary` t├¡nh to├ín doanh sß╗æ dß╗▒ b├ío tß╗òng theo c├┤ng thß╗⌐c: `Forecast Amount = Value * Win Probability / 100`. |
| **3. ─Éiß╗üu kiß╗çn bß║»t buß╗Öc rß╗¥i giai ─æoß║ín (Exit Conditions)** | Cß║Ñu h├¼nh `required_conditions` (dß║íng JSON, VD: `{"min_meetings": 1}`). Khi chuyß╗ân sang giai ─æoß║ín tiß║┐p theo, backend tß╗▒ ─æß╗Öng kiß╗âm tra sß╗æ l╞░ß╗úng cuß╗Öc gß║╖p (`meetings_count`). Nß║┐u ch╞░a ─æß║ít ─æiß╗üu kiß╗çn -> Chß║╖n chuyß╗ân giai ─æoß║ín v├á trß║ú vß╗ü lß╗ùi r├╡ r├áng. |
| **4. Thay ─æß╗òi cß║Ñu h├¼nh kh├┤ng l├ám hß╗Ång c╞í hß╗Öi ─æang chß║íy** | Cß║Ñu h├¼nh giai ─æoß║ín l╞░u `stage_key` ─æß╗Öc lß║¡p v├á sß╗¡ dß╗Ñng `is_active` (soft delete/disable). C╞í hß╗Öi ─æang chß║íy giß╗» nguy├¬n snapshot x├íc suß║Ñt v├á dß╗» liß╗çu lß╗ïch sß╗¡ an to├án. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
S2-09-pipeline-stage-config-backend/
Γö£ΓöÇΓöÇ README.md                           ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ s2_09_pipeline_stages.sql       ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ pipeline_stages.py          ΓåÉ Module quß║ún l├╜ giai ─æoß║ín pipeline & dß╗▒ b├ío doanh sß╗æ
    Γöé   Γö£ΓöÇΓöÇ opportunities.py            ΓåÉ T├¡ch hß╗úp stage key & kiß╗âm tra ─æiß╗üu kiß╗çn chuyß╗ân giai ─æoß║ín
    Γöé   Γö£ΓöÇΓöÇ routes.py                   ΓåÉ API Endpoints
    Γöé   ΓööΓöÇΓöÇ ...
    ΓööΓöÇΓöÇ tests/
        ΓööΓöÇΓöÇ test_pipeline_stages.py     ΓåÉ Automated integration tests
```

---

## ≡ƒôí Chi tiß║┐t API Endpoints

- `GET /api/pipeline-stages` ΓÇö Danh s├ích c├íc giai ─æoß║ín Pipeline & x├íc suß║Ñt thß║»ng
- `POST /api/pipeline-stages` ΓÇö Cß║Ñu h├¼nh tß║ío giai ─æoß║ín mß╗¢i (Sales Manager / Admin)
- `GET /api/pipeline-stages/<id>` ΓÇö Xem chi tiß║┐t 1 giai ─æoß║ín
- `PUT /api/pipeline-stages/<id>` ΓÇö Cß║¡p nhß║¡t giai ─æoß║ín, x├íc suß║Ñt thß║»ng & ─æiß╗üu kiß╗çn (Sales Manager / Admin)
- `DELETE /api/pipeline-stages/<id>` ΓÇö V├┤ hiß╗çu h├│a / X├│a giai ─æoß║ín (Sales Manager / Admin)
- `GET /api/forecast/summary` ΓÇö B├ío c├ío tß╗òng hß╗úp Dß╗▒ b├ío doanh sß╗æ (Weighted Sales Forecast Report)
