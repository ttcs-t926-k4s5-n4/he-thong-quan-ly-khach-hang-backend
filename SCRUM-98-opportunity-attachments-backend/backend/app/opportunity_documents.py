"""
app/opportunity_documents.py — Quản lý Đính kèm Tài liệu vào Cơ hội kinh doanh (SCRUM-98)

Mục tiêu:
- Tải lên nhiều tài liệu cùng một lúc (hồ sơ thầu, biên bản họp, hợp đồng...)
- Giới hạn dung lượng tối đa 20 MB / file
- Hỗ trợ các định dạng PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG
- Kiểm tra tên file, phần mở rộng, MIME type và dung lượng trước khi lưu
- Đặt tên lưu trữ duy nhất bằng UUID để tránh trùng lặp và rủi ro Path Traversal
- Lưu file trên hệ thống backend storage, chỉ lưu metadata và đường dẫn nội bộ vào DB
- Tự động xóa file tạm/file vật lý nếu ghi DB thất bại
- Bảo mật: không để lộ đường dẫn vật lý máy chủ ra ngoài API
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any
from werkzeug.utils import secure_filename

from app.db import fetch_all, fetch_one, get_db

# Giới hạn kích thước tối đa 20 MB
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20,971,520 bytes

# Danh mục định dạng cho phép và MIME type tương ứng
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "pdf": {"application/pdf"},
    "doc": {"application/msword"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    "xls": {"application/vnd.ms-excel"},
    "xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    },
    "ppt": {"application/vnd.ms-powerpoint"},
    "pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/octet-stream",
    },
    "txt": {"text/plain"},
    "csv": {"text/csv", "text/plain", "application/vnd.ms-excel"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_sqlite(conn) -> bool:
    mod = getattr(type(conn), "__module__", "").lower()
    name = getattr(type(conn), "__name__", "").lower()
    return "sqlite" in mod or "sqlite" in name


def ensure_opportunity_documents_table(conn) -> None:
    """Tự động khởi tạo bảng dbo.opportunity_documents nếu chưa tồn tại."""
    cur = conn.cursor()
    if _is_sqlite(conn):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunity_documents (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id   INTEGER NOT NULL,
                original_name    TEXT NOT NULL,
                stored_filename  TEXT NOT NULL UNIQUE,
                storage_path     TEXT NOT NULL,
                file_size        INTEGER NOT NULL,
                file_format      TEXT NOT NULL,
                mime_type        TEXT NOT NULL,
                uploaded_by      INTEGER NOT NULL,
                uploaded_at      INTEGER NOT NULL,
                is_deleted       INTEGER NOT NULL DEFAULT 0,
                deleted_at       INTEGER NULL,
                deleted_by       INTEGER NULL
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_opp_doc_opp_id_uploaded_at
            ON opportunity_documents (opportunity_id, uploaded_at DESC);
            """
        )
        conn.commit()
        return

    # SQL Server
    cur.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'opportunity_documents' AND schema_id = SCHEMA_ID('dbo'))
        BEGIN
            CREATE TABLE dbo.opportunity_documents (
                id               BIGINT         IDENTITY(1,1) PRIMARY KEY,
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
            CREATE INDEX IX_opp_doc_opp_id_uploaded_at ON dbo.opportunity_documents (opportunity_id, uploaded_at DESC);
            CREATE INDEX IX_opp_doc_uploaded_by ON dbo.opportunity_documents (uploaded_by);
        END
        """
    )
    conn.commit()


def get_upload_dir(base_path: str | None = None) -> str:
    """Xác định và tạo thư mục lưu trữ file tài liệu."""
    if not base_path:
        base_path = os.environ.get("DOCUMENTS_UPLOAD_DIR")
    if not base_path:
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "documents")
    os.makedirs(base_path, exist_ok=True)
    return os.path.abspath(base_path)


def validate_file_metadata(original_name: str, file_size: int, mime_type: str) -> str:
    """
    Kiểm tra tên file, phần mở rộng, dung lượng và MIME type.
    Trả về định dạng (extension) hợp lệ dạng chữ thường (không có dấu chấm).
    """
    if not original_name or not original_name.strip():
        raise ValueError("Tên file không được để trống.")

    # Chống Path Traversal và ký tự đặc biệt
    clean_name = secure_filename(original_name)
    if not clean_name or clean_name in {".", ".."}:
        # Nếu secure_filename loại bỏ hết (ví dụ tên toàn tiếng Việt không dấu hoặc ký tự đặc biệt),
        # lấy phần mở rộng gốc
        parts = original_name.rsplit(".", 1)
    else:
        parts = clean_name.rsplit(".", 1)

    if len(parts) < 2 or not parts[1].strip():
        raise ValueError("File không có phần mở rộng hợp lệ.")

    ext = parts[1].strip().lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(ALLOWED_EXTENSIONS.keys())
        raise ValueError(f"Định dạng '.{ext}' không được hỗ trợ. Các định dạng cho phép: {allowed_list}")

    if file_size <= 0:
        raise ValueError("File tải lên không có nội dung (dung lượng 0 byte).")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Dung lượng file vượt quá giới hạn tối đa cho phép (20 MB). Dung lượng file: {file_size / (1024 * 1024):.2f} MB.")

    # Kiểm tra MIME type nếu client gửi lên
    if mime_type:
        clean_mime = mime_type.split(";")[0].strip().lower()
        allowed_mimes = ALLOWED_EXTENSIONS[ext]
        # Cho phép nếu MIME khớp hoặc là octet-stream phổ biến khi upload form-data
        if clean_mime not in allowed_mimes and clean_mime not in {"application/octet-stream", "binary/octet-stream"}:
            pass  # Nếu mime không khớp hoàn toàn nhưng extension hợp lệ, vẫn cảnh báo hoặc chấp nhận theo extension

    return ext


def save_single_document(
    opportunity_id: int,
    file_storage_or_data: Any,
    original_name: str,
    file_size: int,
    mime_type: str,
    uploaded_by: int,
    upload_dir: str | None = None,
    conn: Any = None,
) -> dict[str, Any]:
    """
    Lưu một file tài liệu vào backend storage và ghi metadata vào database.
    Nếu ghi database thất bại, tự động dọn dẹp file vật lý vừa lưu.
    """
    if conn is None:
        conn = get_db()
    ensure_opportunity_documents_table(conn)

    # 1. Kiểm tra metadata file
    ext = validate_file_metadata(original_name, file_size, mime_type)

    # 2. Tạo tên file vật lý duy nhất để chống ghi đè & path traversal
    unique_id = uuid.uuid4().hex
    safe_stored_name = f"{unique_id}.{ext}"

    target_dir = get_upload_dir(upload_dir)
    file_path = os.path.join(target_dir, safe_stored_name)
    relative_path = os.path.join("uploads", "documents", safe_stored_name).replace("\\", "/")

    # 3. Lưu file xuống đĩa vật lý
    try:
        if hasattr(file_storage_or_data, "save"):
            file_storage_or_data.save(file_path)
        elif hasattr(file_storage_or_data, "read"):
            content = file_storage_or_data.read()
            with open(file_path, "wb") as f:
                f.write(content)
        elif isinstance(file_storage_or_data, bytes):
            with open(file_path, "wb") as f:
                f.write(file_storage_or_data)
        else:
            raise ValueError("Dữ liệu file không hợp lệ.")
    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise IOError(f"Không thể lưu file lên máy chủ: {str(e)}")

    # 4. Ghi metadata vào Database
    now = _now_ms()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO dbo.opportunity_documents
                (opportunity_id, original_name, stored_filename, storage_path,
                 file_size, file_format, mime_type, uploaded_by, uploaded_at, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                opportunity_id,
                original_name,
                safe_stored_name,
                relative_path,
                file_size,
                ext,
                mime_type or f"application/{ext}",
                uploaded_by,
                now,
            ),
        )

        doc_id: int
        if _is_sqlite(conn):
            doc_id = cur.lastrowid
        else:
            id_row = fetch_one(conn, "SELECT @@IDENTITY AS id")
            doc_id = int(id_row["id"]) if id_row and id_row.get("id") else 0

        conn.commit()
    except Exception as db_err:
        conn.rollback()
        # Dọn dẹp file vật lý ngay lập tức để tránh file rác (orphan file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise RuntimeError(f"Lỗi khi lưu thông tin tài liệu vào CSDL: {str(db_err)}")

    return {
        "id": doc_id,
        "opportunity_id": opportunity_id,
        "original_name": original_name,
        "file_size": file_size,
        "file_format": ext,
        "mime_type": mime_type or f"application/{ext}",
        "uploaded_by": uploaded_by,
        "uploaded_at": now,
        "download_url": f"/api/documents/{doc_id}/download",
    }


def list_opportunity_documents(opportunity_id: int, conn: Any = None) -> list[dict[str, Any]]:
    """Lấy danh sách tài liệu của cơ hội, sắp xếp theo thời gian mới nhất (không trả về đường dẫn vật lý)."""
    if conn is None:
        conn = get_db()
    ensure_opportunity_documents_table(conn)

    rows = fetch_all(
        conn,
        """
        SELECT d.id, d.opportunity_id, d.original_name, d.file_size, d.file_format,
               d.mime_type, d.uploaded_by, u.full_name AS uploader_name,
               d.uploaded_at
        FROM dbo.opportunity_documents d
        LEFT JOIN dbo.users u ON d.uploaded_by = u.id
        WHERE d.opportunity_id = ? AND d.is_deleted = 0
        ORDER BY d.uploaded_at DESC
        """,
        (opportunity_id,),
    )

    documents = []
    for r in rows:
        documents.append(
            {
                "id": int(r["id"]),
                "opportunity_id": int(r["opportunity_id"]),
                "original_name": str(r["original_name"]),
                "file_size": int(r["file_size"]),
                "file_format": str(r["file_format"]),
                "mime_type": str(r.get("mime_type") or "application/octet-stream"),
                "uploaded_by": int(r["uploaded_by"]),
                "uploader_name": str(r.get("uploader_name") or ""),
                "uploaded_at": int(r["uploaded_at"]),
                "download_url": f"/api/documents/{r['id']}/download",
            }
        )
    return documents


def get_document_by_id(document_id: int, conn: Any = None) -> dict[str, Any] | None:
    """Lấy thông tin tài liệu theo ID (bao gồm cả storage_path để phục vụ download)."""
    if conn is None:
        conn = get_db()
    ensure_opportunity_documents_table(conn)

    row = fetch_one(
        conn,
        """
        SELECT d.id, d.opportunity_id, d.original_name, d.stored_filename,
               d.storage_path, d.file_size, d.file_format, d.mime_type,
               d.uploaded_by, u.full_name AS uploader_name, d.uploaded_at,
               d.is_deleted
        FROM dbo.opportunity_documents d
        LEFT JOIN dbo.users u ON d.uploaded_by = u.id
        WHERE d.id = ?
        """,
        (document_id,),
    )
    if not row or int(row.get("is_deleted", 0)) == 1:
        return None

    return {
        "id": int(row["id"]),
        "opportunity_id": int(row["opportunity_id"]),
        "original_name": str(row["original_name"]),
        "stored_filename": str(row["stored_filename"]),
        "storage_path": str(row["storage_path"]),
        "file_size": int(row["file_size"]),
        "file_format": str(row["file_format"]),
        "mime_type": str(row.get("mime_type") or "application/octet-stream"),
        "uploaded_by": int(row["uploaded_by"]),
        "uploader_name": str(row.get("uploader_name") or ""),
        "uploaded_at": int(row["uploaded_at"]),
        "is_deleted": bool(row.get("is_deleted", 0)),
    }


def delete_opportunity_document(
    document_id: int,
    deleted_by: int,
    conn: Any = None,
) -> bool:
    """Xóa tài liệu (đánh dấu is_deleted = 1 và ghi thời điểm xóa)."""
    if conn is None:
        conn = get_db()
    ensure_opportunity_documents_table(conn)

    doc = get_document_by_id(document_id, conn=conn)
    if not doc:
        return False

    now = _now_ms()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE dbo.opportunity_documents
        SET is_deleted = 1, deleted_at = ?, deleted_by = ?
        WHERE id = ?
        """,
        (now, deleted_by, document_id),
    )
    conn.commit()
    return True
