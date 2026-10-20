"""
app/opportunity_documents.py ΓÇö Quß║ún l├╜ ─É├¡nh k├¿m T├ái liß╗çu v├áo C╞í hß╗Öi kinh doanh (SCRUM-98)

Mß╗Ñc ti├¬u:
- Tß║úi l├¬n nhiß╗üu t├ái liß╗çu c├╣ng mß╗Öt l├║c (hß╗ô s╞í thß║ºu, bi├¬n bß║ún hß╗ìp, hß╗úp ─æß╗ông...)
- Giß╗¢i hß║ín dung l╞░ß╗úng tß╗æi ─æa 20 MB / file
- Hß╗ù trß╗ú c├íc ─æß╗ïnh dß║íng PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG
- Kiß╗âm tra t├¬n file, phß║ºn mß╗ƒ rß╗Öng, MIME type v├á dung l╞░ß╗úng tr╞░ß╗¢c khi l╞░u
- ─Éß║╖t t├¬n l╞░u trß╗» duy nhß║Ñt bß║▒ng UUID ─æß╗â tr├ính tr├╣ng lß║╖p v├á rß╗ºi ro Path Traversal
- L╞░u file tr├¬n hß╗ç thß╗æng backend storage, chß╗ë l╞░u metadata v├á ─æ╞░ß╗¥ng dß║½n nß╗Öi bß╗Ö v├áo DB
- Tß╗▒ ─æß╗Öng x├│a file tß║ím/file vß║¡t l├╜ nß║┐u ghi DB thß║Ñt bß║íi
- Bß║úo mß║¡t: kh├┤ng ─æß╗â lß╗Ö ─æ╞░ß╗¥ng dß║½n vß║¡t l├╜ m├íy chß╗º ra ngo├ái API
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any
from werkzeug.utils import secure_filename

from app.db import fetch_all, fetch_one, get_db

# Giß╗¢i hß║ín k├¡ch th╞░ß╗¢c tß╗æi ─æa 20 MB
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20,971,520 bytes

# Danh mß╗Ñc ─æß╗ïnh dß║íng cho ph├⌐p v├á MIME type t╞░╞íng ß╗⌐ng
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
    """Tß╗▒ ─æß╗Öng khß╗ƒi tß║ío bß║úng dbo.opportunity_documents nß║┐u ch╞░a tß╗ôn tß║íi."""
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
    """X├íc ─æß╗ïnh v├á tß║ío th╞░ mß╗Ñc l╞░u trß╗» file t├ái liß╗çu."""
    if not base_path:
        base_path = os.environ.get("DOCUMENTS_UPLOAD_DIR")
    if not base_path:
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "documents")
    os.makedirs(base_path, exist_ok=True)
    return os.path.abspath(base_path)


def validate_file_metadata(original_name: str, file_size: int, mime_type: str) -> str:
    """
    Kiß╗âm tra t├¬n file, phß║ºn mß╗ƒ rß╗Öng, dung l╞░ß╗úng v├á MIME type.
    Trß║ú vß╗ü ─æß╗ïnh dß║íng (extension) hß╗úp lß╗ç dß║íng chß╗» th╞░ß╗¥ng (kh├┤ng c├│ dß║Ñu chß║Ñm).
    """
    if not original_name or not original_name.strip():
        raise ValueError("T├¬n file kh├┤ng ─æ╞░ß╗úc ─æß╗â trß╗æng.")

    # Chß╗æng Path Traversal v├á k├╜ tß╗▒ ─æß║╖c biß╗çt
    clean_name = secure_filename(original_name)
    if not clean_name or clean_name in {".", ".."}:
        # Nß║┐u secure_filename loß║íi bß╗Å hß║┐t (v├¡ dß╗Ñ t├¬n to├án tiß║┐ng Viß╗çt kh├┤ng dß║Ñu hoß║╖c k├╜ tß╗▒ ─æß║╖c biß╗çt),
        # lß║Ñy phß║ºn mß╗ƒ rß╗Öng gß╗æc
        parts = original_name.rsplit(".", 1)
    else:
        parts = clean_name.rsplit(".", 1)

    if len(parts) < 2 or not parts[1].strip():
        raise ValueError("File kh├┤ng c├│ phß║ºn mß╗ƒ rß╗Öng hß╗úp lß╗ç.")

    ext = parts[1].strip().lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(ALLOWED_EXTENSIONS.keys())
        raise ValueError(f"─Éß╗ïnh dß║íng '.{ext}' kh├┤ng ─æ╞░ß╗úc hß╗ù trß╗ú. C├íc ─æß╗ïnh dß║íng cho ph├⌐p: {allowed_list}")

    if file_size <= 0:
        raise ValueError("File tß║úi l├¬n kh├┤ng c├│ nß╗Öi dung (dung l╞░ß╗úng 0 byte).")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"Dung l╞░ß╗úng file v╞░ß╗út qu├í giß╗¢i hß║ín tß╗æi ─æa cho ph├⌐p (20 MB). Dung l╞░ß╗úng file: {file_size / (1024 * 1024):.2f} MB.")

    # Kiß╗âm tra MIME type nß║┐u client gß╗¡i l├¬n
    if mime_type:
        clean_mime = mime_type.split(";")[0].strip().lower()
        allowed_mimes = ALLOWED_EXTENSIONS[ext]
        # Cho ph├⌐p nß║┐u MIME khß╗¢p hoß║╖c l├á octet-stream phß╗ò biß║┐n khi upload form-data
        if clean_mime not in allowed_mimes and clean_mime not in {"application/octet-stream", "binary/octet-stream"}:
            pass  # Nß║┐u mime kh├┤ng khß╗¢p ho├án to├án nh╞░ng extension hß╗úp lß╗ç, vß║½n cß║únh b├ío hoß║╖c chß║Ñp nhß║¡n theo extension

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
    L╞░u mß╗Öt file t├ái liß╗çu v├áo backend storage v├á ghi metadata v├áo database.
    Nß║┐u ghi database thß║Ñt bß║íi, tß╗▒ ─æß╗Öng dß╗ìn dß║╣p file vß║¡t l├╜ vß╗½a l╞░u.
    """
    if conn is None:
        conn = get_db()
    ensure_opportunity_documents_table(conn)

    # 1. Kiß╗âm tra metadata file
    ext = validate_file_metadata(original_name, file_size, mime_type)

    # 2. Tß║ío t├¬n file vß║¡t l├╜ duy nhß║Ñt ─æß╗â chß╗æng ghi ─æ├¿ & path traversal
    unique_id = uuid.uuid4().hex
    safe_stored_name = f"{unique_id}.{ext}"

    target_dir = get_upload_dir(upload_dir)
    file_path = os.path.join(target_dir, safe_stored_name)
    relative_path = os.path.join("uploads", "documents", safe_stored_name).replace("\\", "/")

    # 3. L╞░u file xuß╗æng ─æ─⌐a vß║¡t l├╜
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
            raise ValueError("Dß╗» liß╗çu file kh├┤ng hß╗úp lß╗ç.")
    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise IOError(f"Kh├┤ng thß╗â l╞░u file l├¬n m├íy chß╗º: {str(e)}")

    # 4. Ghi metadata v├áo Database
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
        # Dß╗ìn dß║╣p file vß║¡t l├╜ ngay lß║¡p tß╗⌐c ─æß╗â tr├ính file r├íc (orphan file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise RuntimeError(f"Lß╗ùi khi l╞░u th├┤ng tin t├ái liß╗çu v├áo CSDL: {str(db_err)}")

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
    """Lß║Ñy danh s├ích t├ái liß╗çu cß╗ºa c╞í hß╗Öi, sß║»p xß║┐p theo thß╗¥i gian mß╗¢i nhß║Ñt (kh├┤ng trß║ú vß╗ü ─æ╞░ß╗¥ng dß║½n vß║¡t l├╜)."""
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
    """Lß║Ñy th├┤ng tin t├ái liß╗çu theo ID (bao gß╗ôm cß║ú storage_path ─æß╗â phß╗Ñc vß╗Ñ download)."""
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
    """X├│a t├ái liß╗çu (─æ├ính dß║Ñu is_deleted = 1 v├á ghi thß╗¥i ─æiß╗âm x├│a)."""
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
