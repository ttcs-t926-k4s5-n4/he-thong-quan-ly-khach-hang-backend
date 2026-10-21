r"""
tests/test_call_logs.py ΓÇö Test suite cho SCRUM-104: Ghi nhanh kß║┐t quß║ú cuß╗Öc gß╗ìi & Tß╗▒ ─æß╗Öng li├¬n kß║┐t C╞í hß╗Öi

Kiß╗âm thß╗¡ to├án diß╗çn 11 y├¬u cß║ºu kß╗╣ thuß║¡t:
1. Tß║ío cuß╗Öc gß╗ìi vß╗¢i dß╗» liß╗çu hß╗úp lß╗ç
2. Thiß║┐u kh├ích h├áng hoß║╖c kh├ích h├áng kh├┤ng tß╗ôn tß║íi (400 / ValueError)
3. Kß║┐t quß║ú cuß╗Öc gß╗ìi kh├┤ng hß╗úp lß╗ç (400 / ValueError)
4. Ghi ch├║ v╞░ß╗út giß╗¢i hß║ín cho ph├⌐p (> 1000 k├╜ tß╗▒)
5. Tß╗▒ ─æß╗Öng li├¬n kß║┐t c╞í hß╗Öi ─æang mß╗ƒ gß║ºn nhß║Ñt
6. Kh├┤ng c├│ c╞í hß╗Öi ─æang mß╗ƒ vß║½n tß║ío ─æ╞░ß╗úc cuß╗Öc gß╗ìi (opportunity_id = None)
7. C╞í hß╗Öi ─æ╞░ß╗úc chß╗ìn kh├┤ng thuß╗Öc kh├ích h├áng ─æ├ú chß╗ìn (400)
8. Tß║ío lß╗ïch gß╗ìi lß║íi (tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc gß╗ìi lß║íi trong tasks)
9. Kh├┤ng tß║ío c├┤ng viß╗çc gß╗ìi lß║íi tr├╣ng khi gß╗¡i lß║íi request (idempotency)
10. Ng╞░ß╗¥i d├╣ng kh├┤ng c├│ quyß╗ün xem hoß║╖c sß╗¡a bß║ún ghi cß╗ºa ng╞░ß╗¥i kh├íc (403)
11. Lß║Ñy lß╗ïch sß╗¡ cuß╗Öc gß╗ìi c├│ ph├ón trang v├á bß╗Ö lß╗ìc
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
    """Kiß╗âm thß╗¡ logic nghiß╗çp vß╗Ñ cß╗ºa Module Ghi nhß║¡n cuß╗Öc gß╗ìi (SCRUM-104)."""

    def test_3_invalid_call_result_raises(self):
        """3. Kß║┐t quß║ú cuß╗Öc gß╗ìi kh├┤ng hß╗úp lß╗ç n├⌐m ValueError."""
        with self.assertRaises(ValueError) as ctx:
            normalize_call_result("invalid_status_xyz")
        self.assertIn("kh├┤ng hß╗úp lß╗ç", str(ctx.exception))

    def test_normalize_call_result_supports_code_and_label(self):
        self.assertEqual(normalize_call_result("connected"), "connected")
        self.assertEqual(normalize_call_result("─É├ú li├¬n hß╗ç th├ánh c├┤ng"), "connected")
        self.assertEqual(normalize_call_result("callback_requested"), "callback_requested")
        self.assertEqual(normalize_call_result("Hß║╣n gß╗ìi lß║íi"), "callback_requested")

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_2_missing_or_nonexistent_customer_raises(self, mock_fetch_one, mock_ensure):
        """2. Kh├ích h├áng kh├┤ng tß╗ôn tß║íi n├⌐m ValueError."""
        mock_fetch_one.return_value = None  # Kh├┤ng t├¼m thß║Ñy kh├ích h├áng
        with self.assertRaises(ValueError) as ctx:
            record_call_log(customer_id=999, call_result="connected", user_id=1, conn=MagicMock())
        self.assertIn("Kh├ích h├áng kh├┤ng tß╗ôn tß║íi", str(ctx.exception))

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_4_notes_exceeding_1000_chars_rejected(self, mock_fetch_one, mock_ensure):
        """4. Ghi ch├║ v╞░ß╗út qu├í 1000 k├╜ tß╗▒ bß╗ï tß╗½ chß╗æi."""
        mock_fetch_one.return_value = {"id": 1, "name": "Kh├ích h├áng Test"}
        long_notes = "A" * 1001

        with self.assertRaises(ValueError) as ctx:
            record_call_log(customer_id=1, call_result="connected", user_id=1, notes=long_notes, conn=MagicMock())
        self.assertIn("v╞░ß╗út qu├í 1000 k├╜ tß╗▒", str(ctx.exception))

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_all")
    def test_5_auto_links_nearest_open_opportunity(self, mock_fetch_all, mock_ensure):
        """5. Tß╗▒ ─æß╗Öng li├¬n kß║┐t c╞í hß╗Öi ─æang mß╗ƒ gß║ºn nhß║Ñt."""
        mock_conn = MagicMock()
        mock_fetch_all.return_value = [
            {"id": 88, "title": "C╞í hß╗Öi mß╗¢i nhß║Ñt", "stage": "─É├ám ph├ín", "customer_id": 5}
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
        """6. Kh├┤ng c├│ c╞í hß╗Öi ─æang mß╗ƒ vß║½n tß║ío ─æ╞░ß╗úc cuß╗Öc gß╗ìi th├ánh c├┤ng (opportunity_id ─æß╗â trß╗æng)."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 10, "name": "Kh├ích h├áng Kh├┤ng C╞í hß╗Öi"},  # customer
            {"id": 201},  # @@IDENTITY
        ]
        mock_find_opp.return_value = None  # Kh├┤ng c├│ c╞í hß╗Öi n├áo
        mock_get_call.return_value = {"id": 201, "customer_id": 10, "opportunity_id": None, "call_result": "no_answer"}

        res = record_call_log(customer_id=10, call_result="no_answer", user_id=1, conn=mock_conn)
        self.assertIsNone(res["opportunity_id"])
        self.assertEqual(res["customer_id"], 10)

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.fetch_one")
    def test_7_opportunity_does_not_belong_to_customer_rejected(self, mock_fetch_one, mock_ensure):
        """7. C╞í hß╗Öi ─æ╞░ß╗úc chß╗ìn kh├┤ng thuß╗Öc kh├ích h├áng ─æ├ú chß╗ìn n├⌐m lß╗ùi."""
        mock_conn = MagicMock()
        mock_fetch_one.side_effect = [
            {"id": 10, "name": "Kh├ích h├áng A"},  # customer_id = 10
            {"id": 99, "customer_id": 20, "title": "C╞í hß╗Öi cß╗ºa Kh├ích h├áng B"},  # opp thuß╗Öc customer 20
        ]

        with self.assertRaises(ValueError) as ctx:
            record_call_log(
                customer_id=10,
                call_result="connected",
                user_id=1,
                opportunity_id=99,
                conn=mock_conn,
            )
        self.assertIn("kh├┤ng thuß╗Öc kh├ích h├áng ─æ├ú chß╗ìn", str(ctx.exception))

    @patch("app.call_logs.create_task")
    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    @patch("app.call_logs.fetch_one")
    def test_8_creates_callback_task(self, mock_fetch_one, mock_get_call, mock_ensure, mock_create_task):
        """8. Tß║ío lß╗ïch gß╗ìi lß║íi (callback_at) sß║╜ tß╗▒ ─æß╗Öng tß║ío c├┤ng viß╗çc trong tasks."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 5, "name": "Kh├ích h├áng VIP"},  # customer
            None,  # existing_task is None
            {"id": 301},  # @@IDENTITY
        ]
        mock_create_task.return_value = {"id": 55, "title": "Gß╗ìi lß║íi cho kh├ích h├áng"}
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
        """9. Kh├┤ng tß║ío c├┤ng viß╗çc gß╗ìi lß║íi tr├╣ng nß║┐u ─æ├ú c├│ task t╞░╞íng ß╗⌐ng."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_fetch_one.side_effect = [
            {"id": 5, "name": "Kh├ích h├áng VIP"},  # customer
            {"id": 55},  # ─É├â C├ô TASK TR╞»ß╗ÜC ─É├ô
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

        # KH├öNG ─É╞»ß╗óC gß╗ìi create_task lß║ºn nß╗»a
        mock_create_task.assert_not_called()
        self.assertEqual(res["callback_task_id"], 55)

    @patch("app.call_logs.ensure_call_logs_table")
    @patch("app.call_logs.get_call_log_by_id")
    def test_10_update_forbidden_for_other_user(self, mock_get_call, mock_ensure):
        """10. Ng╞░ß╗¥i d├╣ng kh├┤ng c├│ quyß╗ün sß╗¡a bß║ún ghi cß╗ºa ng╞░ß╗¥i kh├íc (n├⌐m PermissionError)."""
        mock_get_call.return_value = {"id": 1, "user_id": 10}  # Do user 10 tß║ío

        with self.assertRaises(PermissionError) as ctx:
            # User 99 (employee) cß╗æ sß╗¡a bß║ún ghi cß╗ºa user 10
            update_call_log(call_id=1, user_id=99, user_role="employee", notes="Hack note", conn=MagicMock())
        self.assertIn("kh├┤ng c├│ quyß╗ün", str(ctx.exception))


class TestCallLogsEndpoints(unittest.TestCase):
    """Kiß╗âm thß╗¡ API endpoints cho SCRUM-104."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum104"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.record_call_log")
    def test_1_create_call_log_endpoint_success(self, mock_record, mock_auth):
        """1. Tß║ío cuß╗Öc gß╗ìi vß╗¢i dß╗» liß╗çu hß╗úp lß╗ç qua API."""
        mock_auth.return_value = CurrentUser(2, "sales@test.com", "Sales Rep", "employee", 1)
        mock_record.return_value = {
            "id": 1,
            "customer_id": 5,
            "call_result": "connected",
            "opportunity_id": 12,
            "notes": "Kh├ích h├áng muß╗æn demo v├áo thß╗⌐ 3",
        }

        resp = self.client.post(
            "/api/calls",
            json={
                "customer_id": 5,
                "call_result": "connected",
                "notes": "Kh├ích h├áng muß╗æn demo v├áo thß╗⌐ 3",
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("Ghi nhß║¡n kß║┐t quß║ú cuß╗Öc gß╗ìi th├ánh c├┤ng", data["message"])
        self.assertEqual(data["call_log"]["call_result"], "connected")

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_customer_call_history")
    def test_11_customer_call_history_with_pagination(self, mock_list, mock_auth):
        """11. Lß║Ñy lß╗ïch sß╗¡ cuß╗Öc gß╗ìi cß╗ºa kh├ích h├áng c├│ ph├ón trang."""
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
        """10b. Ng╞░ß╗¥i d├╣ng kh├┤ng c├│ quyß╗ün xem bß║ún ghi cß╗ºa ng╞░ß╗¥i kh├íc qua API trß║ú vß╗ü 403."""
        mock_auth.return_value = CurrentUser(99, "other@test.com", "Other", "employee", 1)
        mock_get_call.return_value = {"id": 1, "user_id": 5}  # Thuß╗Öc user 5

        resp = self.client.get("/api/calls/1")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("kh├┤ng c├│ quyß╗ün", resp.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
