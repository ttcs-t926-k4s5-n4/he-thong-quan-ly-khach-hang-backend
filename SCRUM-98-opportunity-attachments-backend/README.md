# SCRUM-98: Đính kèm Tài liệu vào Cơ hội kinh doanh (Opportunity Documents) — Backend Python

## 📌 1. User Story & Tổng quan

> **"Là Nhân viên kinh doanh, tôi muốn đính kèm tài liệu vào cơ hội, để hồ sơ thầu và biên bản họp nằm cùng chỗ với thương vụ."**

Tính năng này cung cấp giải pháp lưu trữ và quản lý tập tin an toàn cho cơ hội kinh doanh:
- Cho phép tải lên nhiều file cùng một lúc (hồ sơ thầu, biên bản họp, hợp đồng, báo giá...).
- Giới hạn dung lượng tối đa 20 MB / file.
- Định dạng hỗ trợ: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG.
- Lưu trữ file vật lý trên Backend Storage (`uploads/documents`), chỉ lưu metadata và đường dẫn nội bộ vào CSDL.
- Tự động xóa file vật lý nếu ghi CSDL thất bại (chống file rác).
- Bảo mật: kiểm tra phân quyền truy cập cơ hội trên mỗi request tải xuống; không để lộ đường dẫn vật lý máy chủ ra ngoài API; chống Path Traversal bằng UUID.

---

## 📂 2. Cấu trúc thư mục Feature

```
SCRUM-98-opportunity-attachments-backend/
├── README.md                                    ← Tài liệu đặc tả và hướng dẫn chi tiết
├── database/
│   └── scrum_98_opportunity_attachments.sql   ← Migration CSDL: bảng dbo.opportunity_documents
└── backend/
    ├── app/
    │   ├── opportunity_documents.py             ← ★ Module chính: Quản lý upload, validate & download tài liệu
    │   ├── opportunities.py                     ← Module Cơ hội kinh doanh
    │   ├── opportunity_shares.py                ← Ma trận phân quyền sở hữu & chia sẻ (SCRUM-97)
    │   ├── routes.py                            ← REST API Endpoints (/documents)
    │   └── ...                                  ← Các module hiện có của hệ thống
    └── tests/
        ├── conftest.py
        └── test_opportunity_documents.py       ← ★ Bộ kiểm thử tự động toàn diện (11 test cases)
```

---

## 🗄️ 3. Database Schema (`dbo.opportunity_documents`)

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

## 📡 4. Chi tiết API Endpoints

### 1. `POST /api/opportunities/<opportunity_id>/documents`
- **Mô tả**: Tải lên một hoặc nhiều tài liệu đính kèm.
- **Content-Type**: `multipart/form-data`
- **Headers**: `Cookie: auth_token=<token>` (hoặc JWT)
- **Form-data**: `files` (chọn 1 hoặc nhiều file)
- **Response mẫu (201 Created)**:
```json
{
  "message": "Đã tải lên thành công 2 tài liệu.",
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
- **Mô tả**: Lấy danh sách tài liệu đính kèm của cơ hội (sắp xếp mới nhất).
- **Response mẫu (200 OK)**:
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
      "uploader_name": "Nguyễn Văn A",
      "uploaded_at": 1729334400000,
      "download_url": "/api/documents/1/download"
    }
  ]
}
```

### 3. `GET /api/documents/<document_id>/download`
- **Mô tả**: Tải file tài liệu về máy khách (xác minh quyền đọc của cơ hội trên từng request).
- **Response**: Stream file nhị phân với header `Content-Disposition: attachment; filename="ho_so_thau_goi_1.pdf"`.

### 4. `DELETE /api/documents/<document_id>`
- **Mô tả**: Xóa tài liệu (chỉ người tải lên, chủ cơ hội hoặc trưởng nhóm/admin).
- **Response mẫu (200 OK)**: `{"message": "Đã xóa tài liệu thành công."}`
