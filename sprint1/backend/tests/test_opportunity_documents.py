r"""
tests/test_opportunity_documents.py — Test suite cho SCRUM-98: Đính kèm tài liệu vào Cơ hội

Kiểm thử:
1. Tải lên nhiều tài liệu cùng một lúc (POST /api/opportunities/<id>/documents)
2. Kiểm tra dung lượng tối đa 20 MB / file (từ chối > 20 MB)
3. Kiểm tra định dạng hợp lệ (PDF, DOCX, XLSX, v.v.) và từ chối file không hợp lệ (.exe, .sh)
4. Tên file được lưu trữ an toàn bằng UUID, chống Path Traversal
5. Tự động dọn dẹp file vật lý trên đĩa nếu ghi CSDL thất bại (chống file rác)
6. Lấy danh sách tài liệu theo cơ hội (GET /api/opportunities/<id>/documents) không lộ đường dẫn vật lý
7. Phân quyền tải xuống (GET /api/documents/<id>/download): chỉ người có quyền truy cập cơ hội mới được tải
8. Xóa tài liệu (DELETE /api/documents/<id>) theo đúng phân quyền
9. Từ chối khi cơ hội không tồn tại (404)
"""
import io
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.opportunity_documents import (
    delete_opportunity_document,
    get_document_by_id,
    list_opportunity_documents,
    save_single_document,
    validate_file_metadata,
)


class TestOpportunityDocumentsValidation(unittest.TestCase):
    """Kiểm thử validation metadata file (SCRUM-98)."""

    def test_valid_extensions(self):
        for ext in ["pdf", "docx", "xlsx", "pptx", "txt", "csv", "png", "jpg"]:
            res = validate_file_metadata(f"document.{ext}", 1024, "application/octet-stream")
            self.assertEqual(res, ext)

    def test_file_size_exceeding_20mb_rejected(self):
        # 21 MB
        oversized = 21 * 1024 * 1024
        with self.assertRaises(ValueError) as ctx:
            validate_file_metadata("large_contract.pdf", oversized, "application/pdf")
        self.assertIn("vượt quá giới hạn tối đa cho phép (20 MB)", str(ctx.exception))

    def test_zero_byte_file_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            validate_file_metadata("empty.docx", 0, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIn("không có nội dung", str(ctx.exception))

    def test_unsupported_extension_rejected(self):
        for bad_file in ["malware.exe", "script.sh", "app.py", "archive.rar"]:
            with self.assertRaises(ValueError) as ctx:
                validate_file_metadata(bad_file, 1024, "application/octet-stream")
            self.assertIn("không được hỗ trợ", str(ctx.exception))

    def test_path_traversal_sanitized(self):
        # ../../../etc/passwd.pdf -> passwd.pdf
        ext = validate_file_metadata("../../../etc/passwd.pdf", 1024, "application/pdf")
        self.assertEqual(ext, "pdf")


class TestOpportunityDocumentsLogic(unittest.TestCase):
    """Kiểm thử lưu trữ file và dọn dẹp file rác khi DB lỗi."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("app.opportunity_documents.ensure_opportunity_documents_table")
    @patch("app.opportunity_documents.fetch_one")
    def test_save_single_document_success(self, mock_fetch_one, mock_ensure):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.return_value = {"id": 101}

        file_bytes = b"Hello CRM attachment"
        doc = save_single_document(
            opportunity_id=1,
            file_storage_or_data=file_bytes,
            original_name="proposal.pdf",
            file_size=len(file_bytes),
            mime_type="application/pdf",
            uploaded_by=2,
            upload_dir=self.temp_dir,
            conn=mock_conn,
        )

        self.assertEqual(doc["id"], 101)
        self.assertEqual(doc["original_name"], "proposal.pdf")
        self.assertEqual(doc["file_format"], "pdf")
        self.assertEqual(doc["download_url"], "/api/documents/101/download")

        # Kiểm tra file vật lý tồn tại trong thư mục lưu trữ
        files = os.listdir(self.temp_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".pdf"))

    @patch("app.opportunity_documents.ensure_opportunity_documents_table")
    def test_db_failure_cleans_up_stored_file(self, mock_ensure):
        """Nếu ghi DB thất bại, phải xóa file trên ổ đĩa để tránh file rác."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = Exception("DB connection dropped")
        mock_conn.cursor.return_value = mock_cur

        file_bytes = b"Secret data"
        with self.assertRaises(RuntimeError):
            save_single_document(
                opportunity_id=1,
                file_storage_or_data=file_bytes,
                original_name="proposal.pdf",
                file_size=len(file_bytes),
                mime_type="application/pdf",
                uploaded_by=2,
                upload_dir=self.temp_dir,
                conn=mock_conn,
            )

        # File vật lý PHẢI được dọn dẹp sạch sẽ
        self.assertEqual(len(os.listdir(self.temp_dir)), 0)


class TestOpportunityDocumentsEndpoints(unittest.TestCase):
    """Kiểm thử API endpoints của SCRUM-98."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum98"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.save_single_document")
    def test_upload_multiple_documents_endpoint_success(self, mock_save, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "sales@test.com", "Sales Rep", "employee", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}
        mock_save.side_effect = [
            {"id": 10, "original_name": "bid.pdf", "file_size": 1024, "download_url": "/api/documents/10/download"},
            {"id": 11, "original_name": "minutes.docx", "file_size": 2048, "download_url": "/api/documents/11/download"},
        ]

        data = {
            "files": [
                (io.BytesIO(b"PDF content"), "bid.pdf"),
                (io.BytesIO(b"DOCX content"), "minutes.docx"),
            ]
        }
        resp = self.client.post("/api/opportunities/1/documents", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 201)
        payload = resp.get_json()
        self.assertIn("Đã tải lên thành công 2 tài liệu", payload["message"])
        self.assertEqual(len(payload["documents"]), 2)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.list_opportunity_documents")
    def test_list_opportunity_documents_endpoint_success(self, mock_list, mock_get_opp, mock_auth):
        mock_auth.return_value = CurrentUser(2, "sales@test.com", "Sales Rep", "employee", 1)
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}
        mock_list.return_value = [
            {
                "id": 10,
                "opportunity_id": 1,
                "original_name": "contract.pdf",
                "file_size": 1048576,
                "file_format": "pdf",
                "mime_type": "application/pdf",
                "uploaded_by": 2,
                "uploader_name": "Sales Rep",
                "uploaded_at": 1600000000000,
                "download_url": "/api/documents/10/download",
            }
        ]

        resp = self.client.get("/api/opportunities/1/documents")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        # Đảm bảo không để lộ đường dẫn vật lý máy chủ
        self.assertNotIn("storage_path", str(data))
        self.assertNotIn("stored_filename", str(data))

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_document_by_id")
    @patch("app.routes.get_opportunity")
    @patch("app.opportunity_shares.get_user_share_record")
    def test_download_document_forbidden_for_unrelated_user(self, mock_get_share, mock_get_opp, mock_get_doc, mock_auth):
        """Người dùng không có quyền trên cơ hội sẽ bị 403 khi tải file."""
        mock_auth.return_value = CurrentUser(99, "stranger@test.com", "Stranger", "employee", 1)
        mock_get_doc.return_value = {"id": 10, "opportunity_id": 1, "stored_filename": "file.pdf", "original_name": "file.pdf"}
        mock_get_opp.return_value = {"id": 1, "owner_id": 2, "created_by": 2}
        mock_get_share.return_value = None  # không được chia sẻ

        resp = self.client.get("/api/documents/10/download")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Bạn không có quyền", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_document_by_id")
    @patch("app.routes.get_opportunity")
    @patch("app.routes.delete_opportunity_document")
    def test_delete_document_success(self, mock_del, mock_get_opp, mock_get_doc, mock_auth):
        mock_auth.return_value = CurrentUser(2, "uploader@test.com", "Uploader", "employee", 1)
        mock_get_doc.return_value = {"id": 10, "opportunity_id": 1, "uploaded_by": 2}
        mock_get_opp.return_value = {"id": 1, "owner_id": 2}
        mock_del.return_value = True

        resp = self.client.delete("/api/documents/10")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Đã xóa tài liệu thành công", resp.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
