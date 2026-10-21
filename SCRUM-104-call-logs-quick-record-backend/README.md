# SCRUM-104: Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi (Call Logs & Mobile Quick Record) ΓÇö Backend Python

## ≡ƒôî 1. User Story & Tß╗òng quan

> **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi ngay tr├¬n ─æiß╗çn thoß║íi, ─æß╗â ghi lß║íi khi c├▓n nhß╗¢ thay v├¼ ─æß╗â tß╗æi vß╗ü qu├¬n mß║Ñt."**

T├¡nh n─âng n├áy cung cß║Ñp RESTful API phß╗Ñc vß╗Ñ giao diß╗çn mobile/web thao t├íc nhanh:
- Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi vß╗¢i kh├ích h├áng (`─É├ú li├¬n hß╗ç th├ánh c├┤ng`, `Kh├┤ng nghe m├íy`, `Hß║╣n gß╗ìi lß║íi`, `Kh├ích h├áng quan t├óm`...).
- **Tß╗▒ ─æß╗Öng li├¬n kß║┐t C╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt**: nß║┐u nh├ón vi├¬n kh├┤ng chß╗ìn c╞í hß╗Öi, hß╗ç thß╗æng tß╗▒ ─æß╗Öng t├¼m c╞í hß╗Öi ─æang mß╗ƒ mß╗¢i nhß║Ñt cß╗ºa kh├ích h├áng m├á nh├ón vi├¬n c├│ quyß╗ün truy cß║¡p.
- **R├áng buß╗Öc to├án vß║╣n**: nß║┐u ng╞░ß╗¥i d├╣ng chß╗º ─æß╗Öng chß╗ìn c╞í hß╗Öi, backend kiß╗âm tra chß║╖t chß║╜ c╞í hß╗Öi ─æ├│ phß║úi thuß╗Öc ─æ├║ng kh├ích h├áng ─æ├ú chß╗ìn.
- **Lß╗ïch gß╗ìi lß║íi (Callback)**: hß╗ù trß╗ú ─æß║╖t lß╗ïch gß╗ìi lß║íi v├á tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc trong module c├┤ng viß╗çc (`tasks`), ng─ân tß║ío tr├╣ng lß║╖p khi client gß╗¡i lß║íi request.
- **Lß╗ïch sß╗¡ cuß╗Öc gß╗ìi**: tra cß╗⌐u lß╗ïch sß╗¡ cuß╗Öc gß╗ìi theo kh├ích h├áng vß╗¢i ph├ón trang v├á lß╗ìc ─æa ti├¬u ch├¡.

---

## ≡ƒôé 2. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-104-call-logs-quick-record-backend/
Γö£ΓöÇΓöÇ README.md                                    ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_104_call_logs.sql                 ΓåÉ Migration CSDL: bß║úng dbo.call_logs
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ call_logs.py                         ΓåÉ Γÿà Module ch├¡nh: Ghi nhanh cuß╗Öc gß╗ìi & li├¬n kß║┐t c╞í hß╗Öi
    Γöé   Γö£ΓöÇΓöÇ tasks_reminders.py                   ΓåÉ Module c├┤ng viß╗çc & lß╗ïch gß╗ìi lß║íi
    Γöé   Γö£ΓöÇΓöÇ routes.py                            ΓåÉ REST API Endpoints (/calls, /customers/<id>/calls)
    Γöé   ΓööΓöÇΓöÇ ...                                  ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_call_logs.py                   ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (13 test cases)
```

---

## ≡ƒùä∩╕Å 3. Database Schema (`dbo.call_logs`)

```sql
CREATE TABLE dbo.call_logs (
    id                BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
    customer_id       INT            NOT NULL,
    opportunity_id    INT            NULL,
    user_id           INT            NOT NULL,
    call_result       NVARCHAR(100)  NOT NULL,
    notes             NVARCHAR(1000) NULL,
    called_at         BIGINT         NOT NULL,
    callback_at       BIGINT         NULL,
    callback_task_id  INT            NULL,
    created_at        BIGINT         NOT NULL,
    updated_at        BIGINT         NOT NULL,
    CONSTRAINT FK_call_logs_customer FOREIGN KEY (customer_id) REFERENCES dbo.customers(id) ON DELETE CASCADE,
    CONSTRAINT FK_call_logs_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id),
    CONSTRAINT FK_call_logs_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
    CONSTRAINT FK_call_logs_task FOREIGN KEY (callback_task_id) REFERENCES dbo.tasks(id)
);
```

---

## ≡ƒôí 4. Chi tiß║┐t API Endpoints

### 1. `POST /api/calls`
- **M├┤ tß║ú**: Tß║ío bß║ún ghi cuß╗Öc gß╗ìi nhanh tß╗½ mobile / web.
- **Request Body**:
```json
{
  "customer_id": 5,
  "call_result": "interested",
  "notes": "Kh├ích h├áng rß║Ñt quan t├óm ─æß║┐n giß║úi ph├íp CRM, ─æß╗ü nghß╗ï demo v├áo tuß║ºn sau.",
  "callback_at": 1729420800000
}
```
*(Kh├┤ng truyß╗ün `opportunity_id` ΓåÆ Hß╗ç thß╗æng tß╗▒ ─æß╗Öng t├¼m v├á g├ín c╞í hß╗Öi mß╗ƒ gß║ºn nhß║Ñt cß╗ºa kh├ích h├áng)*

- **Response mß║½u (201 Created)**:
```json
{
  "message": "Ghi nhß║¡n kß║┐t quß║ú cuß╗Öc gß╗ìi th├ánh c├┤ng.",
  "call_log": {
    "id": 1,
    "customer_id": 5,
    "customer_name": "C├┤ng ty TNHH Nam Viß╗çt",
    "opportunity_id": 12,
    "opportunity_title": "Dß╗▒ ├ín CRM 2026",
    "user_id": 2,
    "caller_name": "Nguyß╗àn V─ân A",
    "call_result": "interested",
    "call_result_label": "Kh├ích h├áng quan t├óm",
    "notes": "Kh├ích h├áng rß║Ñt quan t├óm ─æß║┐n giß║úi ph├íp CRM, ─æß╗ü nghß╗ï demo v├áo tuß║ºn sau.",
    "called_at": 1729334400000,
    "callback_at": 1729420800000,
    "callback_task_id": 8,
    "created_at": 1729334400000,
    "updated_at": 1729334400000
  }
}
```

### 2. `GET /api/customers/<customer_id>/calls`
- **M├┤ tß║ú**: Lß║Ñy lß╗ïch sß╗¡ cuß╗Öc gß╗ìi cß╗ºa kh├ích h├áng vß╗¢i ph├ón trang v├á bß╗Ö lß╗ìc.
- **Query params**: `page`, `per_page`, `call_result`, `from_date`, `to_date`.
- **Response mß║½u (200 OK)**:
```json
{
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "customer_id": 5,
      "caller_name": "Nguyß╗àn V─ân A",
      "call_result": "interested",
      "call_result_label": "Kh├ích h├áng quan t├óm",
      "opportunity_title": "Dß╗▒ ├ín CRM 2026",
      "notes": "Kh├ích h├áng rß║Ñt quan t├óm...",
      "called_at": 1729334400000
    }
  ]
}
```

### 3. `GET /api/calls/<call_id>`
- **M├┤ tß║ú**: Xem chi tiß║┐t bß║ún ghi cuß╗Öc gß╗ìi (ng╞░ß╗¥i gß╗ìi hoß║╖c quß║ún l├╜).

### 4. `PATCH /api/calls/<call_id>`
- **M├┤ tß║ú**: Cß║¡p nhß║¡t ghi ch├║ hoß║╖c kß║┐t quß║ú cuß╗Öc gß╗ìi (chß╗ë ng╞░ß╗¥i tß║ío hoß║╖c quß║ún l├╜).
