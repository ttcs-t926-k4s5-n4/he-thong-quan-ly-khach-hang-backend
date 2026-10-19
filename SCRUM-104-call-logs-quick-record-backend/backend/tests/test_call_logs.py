r"""
tests/test_call_logs.py — Test suite cho SCRUM-104: Ghi nhanh kết quả cuộc gọi & Tự động liên kết Cơ hội

Kiểm thử toàn diện 11 yêu cầu kỹ thuật:
1. Tạo cuộc gọi với dữ liệu hợp lệ
2. Thiếu khách hàng hoặc khách hàng không tồn tại (400 / ValueError)
3. Kết quả cuộc gọi không hợp lệ (400 / ValueError)
4. Ghi chú vượt giới hạn cho phép (> 1000 ký tự)
5. Tự động liên kết cơ hội đang mở gần nhất
6. Không có cơ hội đang mở vẫn tạo được cuộc gọi (opportunity_id = None)
7. Cơ hội được chọn không thuộc khách hàng đã chọn (400)
8. Tạo lịch gọi lại (tự động tạo công việc gọi lại trong tasks)
9. Không tạo công việc gọi lại trùng khi gửi lại request (idempotency)
10. Người dùng không có quyền xem hoặc sửa bản ghi của người khác (403)
11. Lấy lịch sử cuộc gọi có phân trang và bộ lọc
"""
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.call_logs import (
    find_nearest_open_opportunity,
    get_call_log_by_id,
    list_customer_call_history,
    normalize_call_result,
    record_call_log,
    update_call_log,
)


class TestCallLogsUnit(unittest.TestCase):
    """Kiểm thử logic nghiệp vụ của Module Ghi nhận cuộc gọi (SCRUM-104)."""

    def test_3_invalid_call_result_raises(self):
        """3. Kết quả cuộc gọi không hợp lệ ném ValueError."""
        with self.assertRaises(ValueError) as ctx:
            normalize_call_result("invalid_status_xyz")
        self.assertIn("không hợp lệ", str(ctx.exception))

    def test_normalize_call_result_supports_code_and_label(self):
        self.assertEqual(normalize_call_result("connected"), "connected")
        self.assertEqual(normalize_call_result("Đã liên hệ thành công"), "connected")
        self.assertEqual(normalize_call_result("callback_requested"), "callback_requested")
        self.assertEqual(normalize_call_result("Hẹn gọi lại"), "callback_requested")

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_2_missing_or_nonexistent_customer_raises(self, mock_fetch_one, mock_ensure):
        """2. Khách hàng không tồn tại ném ValueError."""
        mock_fetch_one.return_value = None  # Không tìm thấy khách hàng
        with self.assertRaises(ValueError) as ctx:
            record_call_log(customer_id=999, call_result="connected", user_id=1, conn=MagicMock())
        self.assertIn("Khách hàng không tồn tại", str(ctx.exception))

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_4_notes_exceeding_1000_chars_rejected(self, mock_fetch_one, mock_ensure):
        """4. Ghi chú vượt quá 1000 ký tự bị từ chối."""
        mock_fetch_one.return_value = {"id": 1, "name": "Khách hàng Test"}
        long_notes = "A" * 1001

        with self.assertRaises(ValueError) as ctx:
            record_call_log(customer_id=1, call_result="connected", user_id=1, notes=long_notes, conn=MagicMock())
        self.assertIn("vượt quá 1000 ký tự", str(ctx.exception))

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_all")
    def test_5_auto_links_nearest_open_opportunity(self, mock_fetch_all, mock_ensure):
        """5. Tự động liên kết cơ hội đang mở gần nhất."""
        mock_conn = MagicMock()
        mock_fetch_all.return_value = [
            {"id": 88, "title": "Cơ hội mới nhất", "stage": "Đàm phán", "customer_id": 5}
        ]

        opp = find_nearest_open_opportunity(mock_conn, customer_id=5, user_id=2, user_role="employee")
        self.assertIsNotNone(opp)
        self.assertEqual(opp["id"], 88)

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    @patch("app.call_logs.find_nearest_open_opportunity")
    @patch("app.call_logs.fetch_one")
    def test_6_no_open_opportunity_still_creates_call_log(
        self, mock_fetch_one, mock_find_opp, mock_get_call, mock_ensure
    ):
        """6. Không có cơ hội đang mở vẫn tạo được cuộc gọi thành công (opportunity_id để trống)."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 10, "name": "Khách hàng Không Cơ hội"},  # customer
            {"id": 201},  # @@IDENTITY
        ]
        mock_find_opp.return_value = None  # Không có cơ hội nào
        mock_get_call.return_value = {"id": 201, "customer_id": 10, "opportunity_id": None, "call_result": "no_answer"}

        res = record_call_log(customer_id=10, call_result="no_answer", user_id=1, conn=mock_conn)
        self.assertIsNone(res["opportunity_id"])
        self.assertEqual(res["customer_id"], 10)

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_7_opportunity_does_not_belong_to_customer_rejected(self, mock_fetch_one, mock_ensure):
        """7. Cơ hội được chọn không thuộc khách hàng đã chọn ném lỗi."""
        mock_conn = MagicMock()
        mock_fetch_one.side_effect = [
            {"id": 10, "name": "Khách hàng A"},  # customer_id = 10
            {"id": 99, "customer_id": 20, "title": "Cơ hội của Khách hàng B"},  # opp thuộc customer 20
        ]

        with self.assertRaises(ValueError) as ctx:
            record_call_log(
                customer_id=10,
                call_result="connected",
                user_id=1,
                opportunity_id=99,
                conn=mock_conn,
            )
        self.assertIn("không thuộc khách hàng đã chọn", str(ctx.exception))

    @patch("app.call_logs.create_task")
    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    @patch("app.call_logs.fetch_one")
    def test_8_creates_callback_task(self, mock_fetch_one, mock_get_call, mock_ensure, mock_create_task):
        """8. Tạo lịch gọi lại (callback_at) sẽ tự động tạo công việc trong tasks."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 5, "name": "Khách hàng VIP"},  # customer
            None,  # existing_task is None
            {"id": 301},  # @@IDENTITY
        ]
        mock_create_task.return_value = {"id": 55, "title": "Gọi lại cho khách hàng"}
        mock_get_call.return_value = {"id": 301, "callback_task_id": 55}

        res = record_call_log(
            customer_id=5,
            call_result="callback_requested",
            user_id=2,
            callback_at=1750000000000,
            conn=mock_conn,
        )

        mock_create_task.assert_called_once()
        self.assertEqual(res["callback_task_id"], 55)

    @patch("app.call_logs.create_task")
    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    @patch("app.call_logs.fetch_one")
    def test_9_no_duplicate_callback_task_on_retry(self, mock_fetch_one, mock_get_call, mock_ensure, mock_create_task):
        """9. Không tạo công việc gọi lại trùng nếu đã có task tương ứng."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 5, "name": "Khách hàng VIP"},  # customer
            {"id": 55},  # ĐÃ CÓ TASK TRƯỚC ĐÓ
            {"id": 302},  # @@IDENTITY
        ]
        mock_get_call.return_value = {"id": 302, "callback_task_id": 55}

        res = record_call_log(
            customer_id=5,
            call_result="callback_requested",
            user_id=2,
            callback_at=1750000000000,
            conn=mock_conn,
        )

        # KHÔNG ĐƯỢC gọi create_task lần nữa
        mock_create_task.assert_not_called()
        self.assertEqual(res["callback_task_id"], 55)

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    def test_10_update_forbidden_for_other_user(self, mock_get_call, mock_ensure):
        """10. Người dùng không có quyền sửa bản ghi của người khác (ném PermissionError)."""
        mock_get_call.return_value = {"id": 1, "user_id": 10}  # Do user 10 tạo

        with self.assertRaises(PermissionError) as ctx:
            # User 99 (employee) cố sửa bản ghi của user 10
            update_call_log(call_id=1, user_id=99, user_role="employee", notes="Hack note", conn=MagicMock())
        self.assertIn("không có quyền", str(ctx.exception))


class TestCallLogsEndpoints(unittest.TestCase):
    """Kiểm thử API endpoints cho SCRUM-104."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum104"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.record_call_log")
    def test_1_create_call_log_endpoint_success(self, mock_record, mock_auth):
        """1. Tạo cuộc gọi với dữ liệu hợp lệ qua API."""
        mock_auth.return_value = CurrentUser(2, "sales@test.com", "Sales Rep", "employee", 1)
        mock_record.return_value = {
            "id": 1,
            "customer_id": 5,
            "call_result": "connected",
            "opportunity_id": 12,
            "notes": "Khách hàng muốn demo vào thứ 3",
        }

        resp = self.client.post(
            "/api/calls",
            json={
                "customer_id": 5,
                "call_result": "connected",
                "notes": "Khách hàng muốn demo vào thứ 3",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("Ghi nhận kết quả cuộc gọi thành công", data["message"])
        self.assertEqual(data["call_log"]["call_result"], "connected")

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_customer_call_history")
    def test_11_customer_call_history_with_pagination(self, mock_list, mock_auth):
        """11. Lấy lịch sử cuộc gọi của khách hàng có phân trang."""
        mock_auth.return_value = CurrentUser(2, "sales@test.com", "Sales Rep", "employee", 1)
        mock_list.return_value = {
            "items": [
                {"id": 1, "customer_id": 5, "call_result": "connected", "caller_name": "Sales Rep"}
            ],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "total_pages": 1,
        }

        resp = self.client.get("/api/customers/5/calls?page=1&per_page=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["call_result"], "connected")

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_call_log_by_id")
    def test_calls_get_forbidden_for_other_employee(self, mock_get_call, mock_auth):
        """10b. Người dùng không có quyền xem bản ghi của người khác qua API trả về 403."""
        mock_auth.return_value = CurrentUser(99, "other@test.com", "Other", "employee", 1)
        mock_get_call.return_value = {"id": 1, "user_id": 5}  # Thuộc user 5

        resp = self.client.get("/api/calls/1")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("không có quyền", resp.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
