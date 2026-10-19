# SCRUM-97: Chia sß║╗ C╞í hß╗Öi kinh doanh & Quß║ún l├╜ Sß╗ƒ hß╗»u (Opportunity Sharing & Ownership) ΓÇö Backend Python

## ≡ƒôî 1. Tß╗òng quan Feature

User Story: **"L├á Tr╞░ß╗ƒng nh├│m kinh doanh, t├┤i muß╗æn chia sß║╗ mß╗Öt c╞í hß╗Öi cho nhiß╗üu th├ánh vi├¬n c├╣ng theo d├╡i v├á ghi nhß║¡n hoß║ít ─æß╗Öng, ─æß╗ông thß╗¥i duy tr├¼ mß╗Öt ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh chß╗ïu tr├ích nhiß╗çm vß╗ü c╞í hß╗Öi."**

Feature n├áy mß╗ƒ rß╗Öng m├┤ h├¼nh ph├ón quyß╗ün dß╗» liß╗çu cß╗ºa hß╗ç thß╗æng CRM, cho ph├⌐p ph├ón t├ích vai tr├▓ **Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh (Primary Owner)** v├á **Th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗ (Shared Members)** vß╗¢i c├íc cß║Ñp ─æß╗Ö quyß╗ün hß║ín chi tiß║┐t (`read`, `edit`, `manage`), hß╗ù trß╗ú chuyß╗ân giao quyß╗ün sß╗ƒ hß╗»u nguy├¬n tß╗¡ v├á l╞░u vß║┐t lß╗ïch sß╗¡ kiß╗âm to├ín (SCRUM-95).

---

## ≡ƒöÑ 2. Ma trß║¡n Ph├ón quyß╗ün & Quy tß║»c Nghiß╗çp vß╗Ñ

| Thao t├íc | Admin / Manager | Primary Owner | Shared Member (`manage`) | Shared Member (`edit`) | Shared Member (`read`) | Ng╞░ß╗¥i d├╣ng kh├íc |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Xem c╞í hß╗Öi** | Γ£à | Γ£à | Γ£à | Γ£à | Γ£à | Γ¥î |
| **Cß║¡p nhß║¡t th├┤ng tin c╞í hß╗Öi** | Γ£à | Γ£à | Γ£à | Γ£à | Γ¥î | Γ¥î |
| **Th├¬m / Gß╗í th├ánh vi├¬n chia sß║╗** | Γ£à | Γ£à | Γ£à | Γ¥î | Γ¥î | Γ¥î |
| **Thay ─æß╗òi quyß╗ün th├ánh vi├¬n** | Γ£à | Γ£à | Γ£à | Γ¥î | Γ¥î | Γ¥î |
| **Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh** | Γ£à | Γ£à | Γ¥î | Γ¥î | Γ¥î | Γ¥î |

### Quy tß║»c quan trß╗ìng:
1. **Primary Owner duy nhß║Ñt**: Mß╗ùi c╞í hß╗Öi chß╗ë c├│ mß╗Öt Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh (`owner_id`), l├á ng╞░ß╗¥i chß╗ïu tr├ích nhiß╗çm cao nhß║Ñt.
2. **Kh├┤ng chia sß║╗ cho Primary Owner**: Ng─ân chß║╖n th├¬m tr├╣ng Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh v├áo danh s├ích chia sß║╗.
3. **Ng─ân chia sß║╗ tr├╣ng lß║╖p**: R├áng buß╗Öc duy nhß║Ñt `UNIQUE (opportunity_id, user_id)` bß║úo ─æß║úm t├¡nh to├án vß║╣n dß╗» liß╗çu.
4. **Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u nguy├¬n tß╗¡**:
   - Chß╗ë Primary Owner, Manager hoß║╖c Admin mß╗¢i c├│ quyß╗ün chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh.
   - Cß║¡p nhß║¡t `owner_id` trong `dbo.opportunities`.
   - Nß║┐u chß╗º sß╗ƒ hß╗»u mß╗¢i tr╞░ß╗¢c ─æ├│ l├á Shared Member, tß╗▒ ─æß╗Öng x├│a khß╗Åi bß║úng chia sß║╗.
   - Tß╗▒ ─æß╗Öng th├¬m chß╗º sß╗ƒ hß╗»u c┼⌐ v├áo bß║úng chia sß║╗ vß╗¢i quyß╗ün `edit` ─æß╗â kh├┤ng bß╗ï mß║Ñt quyß╗ün truy cß║¡p.
   - Tß╗▒ ─æß╗Öng ghi nhß║¡t k├╜ v├áo `dbo.opportunity_history` (SCRUM-95) trong c├╣ng transaction.

---

## ≡ƒôé 3. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-97-opportunity-sharing-ownership-backend/
Γö£ΓöÇΓöÇ README.md                                    ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_97_opportunity_shares.sql         ΓåÉ Migration CSDL: bß║úng opportunity_shares + Unique constraint
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ opportunity_shares.py                ΓåÉ Γÿà Module mß╗¢i: Quß║ún l├╜ chia sß║╗ & chuyß╗ân quyß╗ün sß╗ƒ hß╗»u
    Γöé   Γö£ΓöÇΓöÇ opportunity_history.py               ΓåÉ T├¡ch hß╗úp kiß╗âm to├ín lß╗ïch sß╗¡ thay ─æß╗òi (SCRUM-95)
    Γöé   Γö£ΓöÇΓöÇ opportunities.py                     ΓåÉ Module C╞í hß╗Öi
    Γöé   Γö£ΓöÇΓöÇ routes.py                            ΓåÉ API Endpoints (/shares + /transfer-ownership)
    Γöé   ΓööΓöÇΓöÇ ...                                  ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_opportunity_shares.py          ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (15 test cases)
```

---

## ≡ƒùä∩╕Å 4. Database Schema & Migration

### Bß║úng mß╗¢i: `dbo.opportunity_shares`
L╞░u trß╗» danh s├ích c├íc th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗ quyß╗ün truy cß║¡p c╞í hß╗Öi:

| Cß╗Öt | Kiß╗âu dß╗» liß╗çu | R├áng buß╗Öc | M├┤ tß║ú |
|---|---|---|---|
| `id` | `BIGINT` | `IDENTITY(1,1) PRIMARY KEY` | Kh├│a ch├¡nh tß╗▒ t─âng |
| `opportunity_id` | `INT` | `FOREIGN KEY REFERENCES dbo.opportunities(id) ON DELETE CASCADE` | ID c╞í hß╗Öi kinh doanh |
| `user_id` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗ |
| `shared_by` | `INT` | `FOREIGN KEY REFERENCES dbo.users(id)` | ID ng╞░ß╗¥i thß╗▒c hiß╗çn chia sß║╗ |
| `permission_level` | `NVARCHAR(50)` | `NOT NULL DEFAULT 'read'` | Cß║Ñp ─æß╗Ö quyß╗ün: `read`, `edit`, `manage` |
| `created_at` | `BIGINT` | `NOT NULL` | Thß╗¥i ─æiß╗âm chia sß║╗ (UTC epoch ms) |
| `updated_at` | `BIGINT` | `NOT NULL` | Thß╗¥i ─æiß╗âm cß║¡p nhß║¡t (UTC epoch ms) |

### R├áng buß╗Öc & Indexes:
- `UQ_opp_share_user UNIQUE (opportunity_id, user_id)`: Ng─ân chß║╖n chia sß║╗ tr├╣ng mß╗Öt th├ánh vi├¬n trong c├╣ng mß╗Öt c╞í hß╗Öi.
- `IX_opp_shares_opp_id`: Tß╗æi ╞░u truy vß║Ñn danh s├ích th├ánh vi├¬n theo c╞í hß╗Öi.
- `IX_opp_shares_user_id`: Tß╗æi ╞░u lß╗ìc c├íc c╞í hß╗Öi ─æ╞░ß╗úc chia sß║╗ cho mß╗Öt ng╞░ß╗¥i d├╣ng.

---

## ≡ƒôí 5. Chi tiß║┐t API Endpoints

### 1. `GET /api/opportunities/<opportunity_id>/shares`
Lß║Ñy th├┤ng tin Ng╞░ß╗¥i sß╗ƒ hß╗»u ch├¡nh (`primary_owner`) v├á danh s├ích c├íc th├ánh vi├¬n ─æ╞░ß╗úc chia sß║╗ (`shares`).

### 2. `POST /api/opportunities/<opportunity_id>/shares`
Chia sß║╗ c╞í hß╗Öi cho th├ánh vi├¬n mß╗¢i.
- **Request Body**: `{"user_id": 8, "permission_level": "edit"}`
- **Validation**: Kiß╗âm tra ng╞░ß╗¥i d├╣ng tß╗ôn tß║íi, ─æang hoß║ít ─æß╗Öng, kh├┤ng phß║úi l├á Primary Owner v├á ch╞░a tß╗½ng ─æ╞░ß╗úc chia sß║╗.

### 3. `PATCH /api/opportunities/<opportunity_id>/shares/<user_id>`
Cß║¡p nhß║¡t cß║Ñp ─æß╗Ö quyß╗ün hß║ín cß╗ºa th├ánh vi├¬n (`read`, `edit`, `manage`).

### 4. `DELETE /api/opportunities/<opportunity_id>/shares/<user_id>`
Gß╗í th├ánh vi├¬n khß╗Åi c╞í hß╗Öi (cho ph├⌐p ng╞░ß╗¥i quß║ún l├╜ hoß║╖c ch├¡nh th├ánh vi├¬n tß╗▒ rß╗¥i ─æi).

### 5. `POST /api/opportunities/<opportunity_id>/transfer-ownership`
Chuyß╗ân quyß╗ün sß╗ƒ hß╗»u ch├¡nh cho ng╞░ß╗¥i d├╣ng mß╗¢i.
- **Request Body**: `{"new_owner_id": 7}`
- **Validation**: Ng╞░ß╗¥i gß╗ìi phß║úi l├á Primary Owner / Manager / Admin. Chß╗º sß╗ƒ hß╗»u mß╗¢i phß║úi tß╗ôn tß║íi v├á ─æang hoß║ít ─æß╗Öng.
- **Transaction**: Thß╗▒c hiß╗çn cß║¡p nhß║¡t `owner_id`, cß║¡p nhß║¡t bß║úng shares, ghi lß╗ïch sß╗¡ kiß╗âm to├ín `dbo.opportunity_history` trong c├╣ng 1 transaction nguy├¬n tß╗¡.

---

## ≡ƒº¬ 6. H╞░ß╗¢ng dß║½n Chß║íy Kiß╗âm thß╗¡ (Testing)

```bash
cd backend
python -m unittest tests/test_opportunity_shares.py -v
```

Kß║┐t quß║ú: **15/15 tests passed (100% OK)**.
