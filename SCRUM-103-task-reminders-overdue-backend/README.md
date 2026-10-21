# SCRUM-103: Nhß║»c viß╗çc sß║»p ─æß║┐n hß║ín & Xß╗¡ l├╜ viß╗çc qu├í hß║ín (Task Reminders & Overdue) ΓÇö Backend Python

## ≡ƒôî 1. User Story & Tß╗òng quan

> **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn ─æ╞░ß╗úc nhß║»c viß╗çc sß║»p ─æß║┐n hß║ín v├á viß╗çc qu├í hß║ín, ─æß╗â kh├┤ng ─æß╗â c├┤ng viß╗çc bß╗ï bß╗Å qu├¬n v├¼ bß║¡n chß║íy th╞░╞íng vß╗Ñ kh├íc."**

T├¡nh n─âng n├áy triß╗ân khai c╞í chß║┐ tß╗▒ ─æß╗Öng theo d├╡i tiß║┐n ─æß╗Ö v├á cß║únh b├ío thß╗¥i hß║ín c├┤ng viß╗çc:
- Quß║ún l├╜ c├┤ng viß╗çc (tasks) li├¬n kß║┐t vß╗¢i kh├ích h├áng, c╞í hß╗Öi kinh doanh v├á ng╞░ß╗¥i phß╗Ñ tr├ích.
- X├íc ─æß╗ïnh c├┤ng viß╗çc sß║»p ─æß║┐n hß║ín dß╗▒a tr├¬n c├íc mß╗æc nhß║»c tr╞░ß╗¢c linh hoß║ít (`24h`, `1h`...).
- X├íc ─æß╗ïnh c├┤ng viß╗çc qu├í hß║ín (`due_date < now` v├á ch╞░a ho├án th├ánh/hß╗ºy).
- Tß╗▒ ─æß╗Öng tß║ío th├┤ng b├ío trong ß╗⌐ng dß╗Ñng (`notifications`), chß╗æng tß║ío tr├╣ng lß║╖p qua r├áng buß╗Öc Unique Deduplication.
- Cung cß║Ñp API b├ío c├ío thß╗æng k├¬ c├┤ng viß╗çc qu├í hß║ín cß╗ºa tß╗½ng th├ánh vi├¬n cho Tr╞░ß╗ƒng nh├│m/Admin.
- T├íc vß╗Ñ nß╗ün (Background Worker) ─æß╗ïnh kß╗│ qu├⌐t hß║ín c├┤ng viß╗çc m├á kh├┤ng sinh nhiß╗üu scheduler ngo├ái ├╜ muß╗æn khi chß║íy reload.

---

## ≡ƒôé 2. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-103-task-reminders-overdue-backend/
Γö£ΓöÇΓöÇ README.md                                    ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_103_task_reminders_overdue.sql    ΓåÉ Migration CSDL: dbo.tasks, dbo.notifications, dbo.task_reminder_settings
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ tasks_reminders.py                   ΓåÉ Γÿà Module ch├¡nh: Quß║ún l├╜ c├┤ng viß╗çc, nhß║»c hß║ín & th├┤ng b├ío
    Γöé   Γö£ΓöÇΓöÇ routes.py                            ΓåÉ REST API Endpoints (/tasks, /notifications, /teams)
    Γöé   ΓööΓöÇΓöÇ ...                                  ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_task_reminders_overdue.py      ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (11 test cases)
```

---

## ≡ƒùä∩╕Å 3. Database Schema

### 1. Bß║úng `dbo.tasks`
L╞░u trß╗» th├┤ng tin c├┤ng viß╗çc, ph├ón c├┤ng v├á thß╗¥i hß║ín:
- `id`: INT IDENTITY PRIMARY KEY
- `title`: NVARCHAR(250) NOT NULL
- `assigned_to`: INT NOT NULL (FK users)
- `customer_id`: INT NULL (FK customers)
- `opportunity_id`: INT NULL (FK opportunities)
- `due_date`: BIGINT NOT NULL (epoch ms)
- `priority`: NVARCHAR(50) DEFAULT 'medium'
- `status`: NVARCHAR(50) DEFAULT 'pending'

### 2. Bß║úng `dbo.notifications`
L╞░u trß╗» th├┤ng b├ío trong ß╗⌐ng dß╗Ñng cho ng╞░ß╗¥i d├╣ng:
- `id`: BIGINT IDENTITY PRIMARY KEY
- `user_id`: INT NOT NULL (FK users)
- `title`: NVARCHAR(250) NOT NULL
- `message`: NVARCHAR(MAX) NOT NULL
- `type`: NVARCHAR(50) NOT NULL ('task_due_soon', 'task_overdue')
- `reference_type`: NVARCHAR(50) ('task')
- `reference_id`: INT NULL
- `reminder_milestone`: NVARCHAR(50) ('24h', '1h', 'overdue')
- `is_read`: BIT DEFAULT 0

---

## ≡ƒôí 4. Chi tiß║┐t API Endpoints

### 1. `GET /api/tasks/reminders`
- **M├┤ tß║ú**: Lß║Ñy danh s├ích viß╗çc sß║»p ─æß║┐n hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi (c├▓n d╞░ß╗¢i 24h hoß║╖c theo mß╗æc cß║Ñu h├¼nh).
- **Response mß║½u (200 OK)**:
```json
{
  "total": 1,
  "reminders": [
    {
      "id": 1,
      "title": "Gß╗¡i b├ío gi├í hß╗úp ─æß╗ông",
      "due_date": 1729350000000,
      "hours_left": 3.5,
      "priority": "high",
      "status": "pending",
      "customer_name": "C├┤ng ty TNHH Nam Viß╗çt",
      "opportunity_title": "Dß╗▒ ├ín CRM 2026"
    }
  ]
}
```

### 2. `GET /api/tasks/overdue`
- **M├┤ tß║ú**: Lß║Ñy danh s├ích viß╗çc qu├í hß║ín cß╗ºa ng╞░ß╗¥i d├╣ng hiß╗çn tß║íi ─æß╗â hiß╗ân thß╗ï nß╗òi bß║¡t tr├¬n Dashboard.
- **Response mß║½u (200 OK)**:
```json
{
  "total": 1,
  "overdue_tasks": [
    {
      "id": 2,
      "title": "Gß╗ìi lß║íi x├íc nhß║¡n lß╗ïch hß║╣n",
      "due_date": 1729320000000,
      "overdue_hours": 5.2,
      "priority": "medium",
      "status": "in_progress"
    }
  ]
}
```

### 3. `GET /api/notifications`
- **M├┤ tß║ú**: Lß║Ñy danh s├ích th├┤ng b├ío cß╗ºa ng╞░ß╗¥i d├╣ng vß╗¢i ph├ón trang v├á lß╗ìc ch╞░a ─æß╗ìc (`?unread_only=true&page=1&per_page=20`).

### 4. `PATCH /api/notifications/<id>/read`
- **M├┤ tß║ú**: ─É├ính dß║Ñu th├┤ng b├ío ─æ├ú ─æß╗ìc.

### 5. `GET /api/teams/overdue-summary`
- **M├┤ tß║ú**: Thß╗æng k├¬ sß╗æ l╞░ß╗úng viß╗çc qu├í hß║ín theo tß╗½ng th├ánh vi├¬n (Tr╞░ß╗ƒng nh├│m / Admin).
- **Ph├ón quyß╗ün**: Nh├ón vi├¬n th├┤ng th╞░ß╗¥ng bß╗ï tß╗½ chß╗æi vß╗¢i m├ú 403.
- **Response mß║½u (200 OK)**:
```json
{
  "total_members": 2,
  "members": [
    {
      "user_id": 5,
      "full_name": "Trß║ºn V─ân B",
      "email": "b.tran@company.vn",
      "group_name": "Nh├│m Kinh doanh 1",
      "overdue_count": 2,
      "overdue_tasks": [...]
    }
  ]
}
```

### 6. `GET` & `PUT /api/tasks/reminder-settings`
- **M├┤ tß║ú**: Lß║Ñy v├á cß║¡p nhß║¡t mß╗æc nhß║»c tr╞░ß╗¢c hß║ín ─æß╗Öng (`{"milestones": ["48h", "2h", "30m"]}`).
