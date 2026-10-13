# SCRUM-76: Y├¬u cß║ºu Hß╗ù trß╗ú Sau b├ín & Gß║»n cß╗¥ Rß╗ºi ro Rß╗¥i bß╗Å (Backend Python)

## ≡ƒôî Tß╗òng quan Feature

User Story n├áy cung cß║Ñp hß╗ç thß╗æng **Quß║ún l├╜ Y├¬u cß║ºu Hß╗ù trß╗ú Sau b├ín (Support Tickets)** cho bß╗Ö phß║¡n Ch─âm s├│c kh├ích h├áng, kß║┐t hß╗úp vß╗¢i engine **Tß╗▒ ─æß╗Öng Gß║»n cß╗¥ Rß╗ºi ro Rß╗¥i bß╗Å (Churn Risk Flagging)** ΓÇö gi├║p Nh├ón vi├¬n kinh doanh phß╗Ñ tr├ích nhß║¡n cß║únh b├ío kß╗ïp thß╗¥i khi kh├ích h├áng c├│ nguy c╞í mß║Ñt ─æi.

---

## ≡ƒöÑ C├íc Y├¬u cß║ºu & ─É├íp ß╗⌐ng (Requirement Specifications)

| Y├¬u cß║ºu Story | Giß║úi ph├íp & ─É├íp ß╗⌐ng Backend |
|---|---|
| **1. Tß║ío & Quß║ún l├╜ Y├¬u cß║ºu Hß╗ù trß╗ú** | CRUD ─æß║ºy ─æß╗º cho `dbo.support_tickets`. Mß╗ùi ticket c├│: Ti├¬u ─æß╗ü, M├┤ tß║ú, Mß╗⌐c ─æß╗Ö ╞░u ti├¬n (`low`/`medium`/`high`/`urgent`), Trß║íng th├íi (`open`/`in_progress`/`resolved`/`closed`), Ng╞░ß╗¥i xß╗¡ l├╜ (`assignee_id`). |
| **2. Tß╗▒ ─æß╗Öng sinh M├ú ticket** | Mß╗ùi ticket tß║ío mß╗¢i ─æ╞░ß╗úc cß║Ñp m├ú duy nhß║Ñt theo ─æß╗ïnh dß║íng `TK-XXXXXX` (timestamp-based). |
| **3. Engine Gß║»n cß╗¥ Rß╗ºi ro Rß╗¥i bß╗Å (Auto Churn Risk)** | Sau mß╗ùi thao t├íc Tß║ío / Cß║¡p nhß║¡t / X├│a ticket, hß╗ç thß╗æng tß╗▒ ─æß╗Öng gß╗ìi `evaluate_and_update_churn_risk()`. Logic: ΓëÑ 2 ticket tß╗ôn ─æß╗ìng ΓåÆ Gß║»n cß╗¥ rß╗ºi ro. C├│ ticket `urgent` ch╞░a xß╗¡ l├╜ ΓåÆ Gß║»n cß╗¥ rß╗ºi ro khß║⌐n cß║Ñp. |
| **4. G├│c nh├¼n 360┬░ Kh├ích h├áng** | API `GET /api/customers/<id>/360` trß║ú vß╗ü to├án bß╗Ö: Th├┤ng tin kh├ích h├áng + Custom Fields + Danh s├ích Support Tickets + Danh s├ích C╞í hß╗Öi li├¬n quan + Cß║únh b├ío Churn Risk (nß║┐u c├│). |
| **5. Danh s├ích Cß║únh b├ío Rß╗ºi ro** | API `GET /api/churn-risk-alerts` trß║ú vß╗ü danh s├ích tß║Ñt cß║ú kh├ích h├áng ─æang bß╗ï gß║»n cß╗¥ rß╗ºi ro rß╗¥i bß╗Å ─æß╗â NVKD phß╗Ñ tr├ích xß╗¡ l├╜ ngay. |

---

## ≡ƒôé Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-76-support-tickets-backend/
Γö£ΓöÇΓöÇ README.md                                   ΓåÉ T├ái liß╗çu h╞░ß╗¢ng dß║½n & API Spec
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_76_support_tickets.sql            ΓåÉ SQL Schema cho SQL Server 2019+
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ support_tickets.py                  ΓåÉ Γÿà Module mß╗¢i: Support Tickets & Churn Risk Engine
    Γöé   Γö£ΓöÇΓöÇ customers.py                        ΓåÉ T├¡ch hß╗úp cß╗Öt is_churn_risk, churn_risk_reason
    Γöé   Γö£ΓöÇΓöÇ routes.py                           ΓåÉ API Endpoints (th├¬m routes SCRUM-76)
    Γöé   ΓööΓöÇΓöÇ ...
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_support_tickets_churn_risk.py  ΓåÉ Γÿà Test suite mß╗¢i cho SCRUM-76
```

---

## ≡ƒùä∩╕Å Database Schema ΓÇö Thay ─æß╗òi DB

### Bß║úng mß╗¢i: `dbo.support_tickets`
L╞░u trß╗» tß║Ñt cß║ú y├¬u cß║ºu hß╗ù trß╗ú sau b├ín:
- `id` (INT, PK, IDENTITY)
- `ticket_code` (VARCHAR(50), UNIQUE) ΓÇö M├ú ticket tß╗▒ ─æß╗Öng `TK-XXXXXX`
- `customer_id` (INT, FK ΓåÆ `dbo.customers.id`)
- `title` (NVARCHAR(255)) ΓÇö Ti├¬u ─æß╗ü y├¬u cß║ºu hß╗ù trß╗ú
- `description` (NVARCHAR(MAX)) ΓÇö M├┤ tß║ú chi tiß║┐t
- `priority` (VARCHAR(20)) ΓÇö `low` | `medium` | `high` | `urgent`
- `status` (VARCHAR(20)) ΓÇö `open` | `in_progress` | `resolved` | `closed`
- `assignee_id` (INT, FK ΓåÆ `dbo.users.id`) ΓÇö Ng╞░ß╗¥i xß╗¡ l├╜
- `created_by` (INT, FK ΓåÆ `dbo.users.id`)
- `created_at` / `updated_at` (BIGINT, Unix ms)

### Cß╗Öt mß╗¢i trong `dbo.customers`:
- `is_churn_risk` (BIT, default 0) ΓÇö Cß╗¥ rß╗ºi ro rß╗¥i bß╗Å (tß╗▒ ─æß╗Öng cß║¡p nhß║¡t)
- `churn_risk_reason` (NVARCHAR(500)) ΓÇö L├╜ do ─æ╞░ß╗úc gß║»n cß╗¥ rß╗ºi ro
- `last_interaction_at` (BIGINT) ΓÇö Thß╗¥i ─æiß╗âm t╞░╞íng t├íc gß║ºn nhß║Ñt

---

## ≡ƒôí Chi tiß║┐t API Endpoints

### 1. Quß║ún l├╜ Y├¬u cß║ºu Hß╗ù trß╗ú (Support Tickets)
- `GET /api/support-tickets` ΓÇö Danh s├ích & Lß╗ìc ticket
  - Query params: `customer_id`, `status`, `priority`, `assignee_id`, `page`, `per_page`
- `POST /api/support-tickets` ΓÇö Tß║ío ticket mß╗¢i
  - Body: `{ customer_id, title, description, priority, status, assignee_id }`
- `GET /api/support-tickets/<id>` ΓÇö Chi tiß║┐t 1 ticket
- `PUT /api/support-tickets/<id>` ΓÇö Cß║¡p nhß║¡t ticket (─æß╗òi trß║íng th├íi, ng╞░ß╗¥i xß╗¡ l├╜, ...)
- `DELETE /api/support-tickets/<id>` ΓÇö X├│a ticket

### 2. Cß║únh b├ío & G├│c nh├¼n 360┬░
- `GET /api/customers/<id>/360` ΓÇö G├│c nh├¼n 360┬░ Kh├ích h├áng (info + tickets + opportunities + churn alert)
- `GET /api/churn-risk-alerts` ΓÇö Danh s├ích kh├ích h├áng ─æang bß╗ï cß║únh b├ío rß╗ºi ro rß╗¥i bß╗Å

---

## ≡ƒº¬ Kiß╗âm thß╗¡ Tß╗▒ ─æß╗Öng (Automated Testing)

```powershell
cd backend
.venv\Scripts\pytest tests/test_support_tickets_churn_risk.py -v
```

Kß║┐t quß║ú kiß╗âm thß╗¡: **Tß║Ñt cß║ú tests passed (100%)**.
