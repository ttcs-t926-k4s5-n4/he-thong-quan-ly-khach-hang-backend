# SCRUM-98: ─É├¡nh k├¿m T├ái liß╗çu v├áo C╞í hß╗Öi kinh doanh (Opportunity Documents) ΓÇö Backend Python

## ≡ƒôî 1. User Story & Tß╗òng quan

> **"L├á Nh├ón vi├¬n kinh doanh, t├┤i muß╗æn ─æ├¡nh k├¿m t├ái liß╗çu v├áo c╞í hß╗Öi, ─æß╗â hß╗ô s╞í thß║ºu v├á bi├¬n bß║ún hß╗ìp nß║▒m c├╣ng chß╗ù vß╗¢i th╞░╞íng vß╗Ñ."**

T├¡nh n─âng n├áy cung cß║Ñp giß║úi ph├íp l╞░u trß╗» v├á quß║ún l├╜ tß║¡p tin an to├án cho c╞í hß╗Öi kinh doanh:
- Cho ph├⌐p tß║úi l├¬n nhiß╗üu file c├╣ng mß╗Öt l├║c (hß╗ô s╞í thß║ºu, bi├¬n bß║ún hß╗ìp, hß╗úp ─æß╗ông, b├ío gi├í...).
- Giß╗¢i hß║ín dung l╞░ß╗úng tß╗æi ─æa 20 MB / file.
- ─Éß╗ïnh dß║íng hß╗ù trß╗ú: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG.
- L╞░u trß╗» file vß║¡t l├╜ tr├¬n Backend Storage (`uploads/documents`), chß╗ë l╞░u metadata v├á ─æ╞░ß╗¥ng dß║½n nß╗Öi bß╗Ö v├áo CSDL.
- Tß╗▒ ─æß╗Öng x├│a file vß║¡t l├╜ nß║┐u ghi CSDL thß║Ñt bß║íi (chß╗æng file r├íc).
- Bß║úo mß║¡t: kiß╗âm tra ph├ón quyß╗ün truy cß║¡p c╞í hß╗Öi tr├¬n mß╗ùi request tß║úi xuß╗æng; kh├┤ng ─æß╗â lß╗Ö ─æ╞░ß╗¥ng dß║½n vß║¡t l├╜ m├íy chß╗º ra ngo├ái API; chß╗æng Path Traversal bß║▒ng UUID.

---

## ≡ƒôé 2. Cß║Ñu tr├║c th╞░ mß╗Ñc Feature

```
SCRUM-98-opportunity-attachments-backend/
Γö£ΓöÇΓöÇ README.md                                    ΓåÉ T├ái liß╗çu ─æß║╖c tß║ú v├á h╞░ß╗¢ng dß║½n chi tiß║┐t
Γö£ΓöÇΓöÇ database/
Γöé   ΓööΓöÇΓöÇ scrum_98_opportunity_attachments.sql   ΓåÉ Migration CSDL: bß║úng dbo.opportunity_documents
ΓööΓöÇΓöÇ backend/
    Γö£ΓöÇΓöÇ app/
    Γöé   Γö£ΓöÇΓöÇ opportunity_documents.py             ΓåÉ Γÿà Module ch├¡nh: Quß║ún l├╜ upload, validate & download t├ái liß╗çu
    Γöé   Γö£ΓöÇΓöÇ opportunities.py                     ΓåÉ Module C╞í hß╗Öi kinh doanh
    Γöé   Γö£ΓöÇΓöÇ opportunity_shares.py                ΓåÉ Ma trß║¡n ph├ón quyß╗ün sß╗ƒ hß╗»u & chia sß║╗ (SCRUM-97)
    Γöé   Γö£ΓöÇΓöÇ routes.py                            ΓåÉ REST API Endpoints (/documents)
    Γöé   ΓööΓöÇΓöÇ ...                                  ΓåÉ C├íc module hiß╗çn c├│ cß╗ºa hß╗ç thß╗æng
    ΓööΓöÇΓöÇ tests/
        Γö£ΓöÇΓöÇ conftest.py
        ΓööΓöÇΓöÇ test_opportunity_documents.py       ΓåÉ Γÿà Bß╗Ö kiß╗âm thß╗¡ tß╗▒ ─æß╗Öng to├án diß╗çn (11 test cases)
```

---

## ≡ƒùä∩╕Å 3. Database Schema (`dbo.opportunity_documents`)

```sql
CREATE TABLE dbo.opportunity_documents (
    id               BIGINT         IDENTITY(1,1) NOT NULL PRIMARY KEY,
    opportunity_id   INT            NOT NULL,
    original_name    NVARCHAR(255)  NOT NULL,
    stored_filename  NVARCHAR(255)  NOT NULL UNIQUE,
    storage_path     NVARCHAR(500)  NOT NULL,
    file_size        BIGINT         NOT NULL,
    file_format      NVARCHAR(50)   NOT NULL,
    mime_type        NVARCHAR(100)  NOT NULL,
    uploaded_by      INT            NOT NULL,
    uploaded_at      BIGINT         NOT NULL,
    is_deleted       BIT            NOT NULL CONSTRAINT DF_opp_doc_is_deleted DEFAULT (0),
    deleted_at       BIGINT         NULL,
    deleted_by       INT            NULL,
    CONSTRAINT FK_opp_doc_opportunity FOREIGN KEY (opportunity_id) REFERENCES dbo.opportunities(id) ON DELETE CASCADE,
    CONSTRAINT FK_opp_doc_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES dbo.users(id)
);
```

---

## ≡ƒôí 4. Chi tiß║┐t API Endpoints

### 1. `POST /api/opportunities/<opportunity_id>/documents`
- **M├┤ tß║ú**: Tß║úi l├¬n mß╗Öt hoß║╖c nhiß╗üu t├ái liß╗çu ─æ├¡nh k├¿m.
- **Content-Type**: `multipart/form-data`
- **Headers**: `Cookie: auth_token=<token>` (hoß║╖c JWT)
- **Form-data**: `files` (chß╗ìn 1 hoß║╖c nhiß╗üu file)
- **Response mß║½u (201 Created)**:
```json
{
  "message": "─É├ú tß║úi l├¬n th├ánh c├┤ng 2 t├ái liß╗çu.",
  "documents": [
    {
      "id": 1,
      "opportunity_id": 10,
      "original_name": "ho_so_thau_goi_1.pdf",
      "file_size": 2458600,
      "file_format": "pdf",
      "mime_type": "application/pdf",
      "uploaded_by": 2,
      "uploaded_at": 1729334400000,
      "download_url": "/api/documents/1/download"
    }
  ]
}
```

### 2. `GET /api/opportunities/<opportunity_id>/documents`
- **M├┤ tß║ú**: Lß║Ñy danh s├ích t├ái liß╗çu ─æ├¡nh k├¿m cß╗ºa c╞í hß╗Öi (sß║»p xß║┐p mß╗¢i nhß║Ñt).
- **Response mß║½u (200 OK)**:
```json
{
  "opportunity_id": 10,
  "total": 1,
  "documents": [
    {
      "id": 1,
      "opportunity_id": 10,
      "original_name": "ho_so_thau_goi_1.pdf",
      "file_size": 2458600,
      "file_format": "pdf",
      "mime_type": "application/pdf",
      "uploaded_by": 2,
      "uploader_name": "Nguyß╗àn V─ân A",
      "uploaded_at": 1729334400000,
      "download_url": "/api/documents/1/download"
    }
  ]
}
```

### 3. `GET /api/documents/<document_id>/download`
- **M├┤ tß║ú**: Tß║úi file t├ái liß╗çu vß╗ü m├íy kh├ích (x├íc minh quyß╗ün ─æß╗ìc cß╗ºa c╞í hß╗Öi tr├¬n tß╗½ng request).
- **Response**: Stream file nhß╗ï ph├ón vß╗¢i header `Content-Disposition: attachment; filename="ho_so_thau_goi_1.pdf"`.

### 4. `DELETE /api/documents/<document_id>`
- **M├┤ tß║ú**: X├│a t├ái liß╗çu (chß╗ë ng╞░ß╗¥i tß║úi l├¬n, chß╗º c╞í hß╗Öi hoß║╖c tr╞░ß╗ƒng nh├│m/admin).
- **Response mß║½u (200 OK)**: `{"message": "─É├ú x├│a t├ái liß╗çu th├ánh c├┤ng."}`
