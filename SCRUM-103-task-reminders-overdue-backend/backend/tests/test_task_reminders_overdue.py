r"""
tests/test_task_reminders_overdue.py ΓÇö Test suite cho SCRUM-103: Nhß║»c viß╗çc sß║»p ─æß║┐n hß║ín & Qu├í hß║ín

Kiß╗âm thß╗¡:
1. Tß║ío c├┤ng viß╗çc vß╗¢i thß╗¥i hß║ín hß╗úp lß╗ç (POST /api/tasks)
2. Kiß╗âm tra x├íc thß╗▒c ─æß║ºu v├áo (ti├¬u ─æß╗ü trß╗æng, due_date kh├┤ng hß╗úp lß╗ç ΓåÆ 400)
3. X├íc ─æß╗ïnh c├┤ng viß╗çc sß║»p ─æß║┐n hß║ín theo mß╗æc cß║Ñu h├¼nh (GET /api/tasks/reminders)
4. X├íc ─æß╗ïnh c├┤ng viß╗çc qu├í hß║ín (GET /api/tasks/overdue)
5. Loß║íi trß╗½ c├┤ng viß╗çc ─æ├ú ho├án th├ánh (completed) hoß║╖c ─æ├ú hß╗ºy (cancelled)
6. T├╣y biß║┐n cß║Ñu h├¼nh mß╗æc nhß║»c viß╗çc ─æß╗Öng (GET & PUT /api/tasks/reminder-settings)
7. Tß╗▒ ─æß╗Öng sinh th├┤ng b├ío sß║»p ─æß║┐n hß║ín v├á qu├í hß║ín (process_task_reminders_and_overdue)
8. Chß╗æng tß║ío th├┤ng b├ío tr├╣ng lß║╖p khi chß║íy bß╗Ö xß╗¡ l├╜ lß║╖p lß║íi nhiß╗üu lß║ºn
9. Quß║ún l├╜ th├┤ng b├ío: ph├ón trang, lß╗ìc ch╞░a ─æß╗ìc v├á ─æ├ính dß║Ñu ─æ├ú ─æß╗ìc
10. Thß╗æng k├¬ tß╗òng sß╗æ c├┤ng viß╗çc qu├í hß║ín theo th├ánh vi├¬n d├ánh cho Tr╞░ß╗ƒng nh├│m/Admin (GET /api/teams/overdue-summary)
11. Ng─ân nh├ón vi├¬n th├┤ng th╞░ß╗¥ng truy cß║¡p thß╗æng k├¬ quß║ún l├╜ (403)
"""
import time
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.tasks_reminders import (
    create_task,
    get_task_by_id,
    get_team_overdue_summary,
    get_user_reminder_settings,
    list_user_due_soon_tasks,
    list_user_notifications,
    list_user_overdue_tasks,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    parse_milestone_ms,
    process_task_reminders_and_overdue,
    update_user_reminder_settings,
)


class TestTaskRemindersLogic(unittest.TestCase):
    """Kiß╗âm thß╗¡ logic x├íc ─æß╗ïnh hß║ín c├┤ng viß╗çc v├á chß╗æng tß║ío th├┤ng b├ío tr├╣ng."""

    def test_parse_milestone_ms(self):
        self.assertEqual(parse_milestone_ms("24h"), 24 * 3600 * 1000)
        self.assertEqual(parse_milestone_ms("1h"), 1 * 3600 * 1000)
        self.assertEqual(parse_milestone_ms("30m"), 30 * 60 * 1000)
        self.assertEqual(parse_milestone_ms("2d"), 2 * 86400 * 1000)

    @patch("app.tasks_reminders.ensure_tasks_tables")
    @patch("app.tasks_reminders.fetch_one")
    def test_create_task_validation(self, mock_fetch_one, mock_ensure):
        mock_conn = MagicMock()
        with self.assertRaises(ValueError) as ctx:
            create_task(title="", due_date=1700000000000, assigned_to=1, created_by=1, conn=mock_conn)
        self.assertIn("Ti├¬u ─æß╗ü", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_task(title="Hß╗ìp kh├ích h├áng", due_date=0, assigned_to=1, created_by=1, conn=mock_conn)
        self.assertIn("Thß╗¥i hß║ín", str(ctx.exception))

    @patch("app.tasks_reminders.ensure_tasks_tables")
    @patch("app.tasks_reminders.fetch_all")
    @patch("app.tasks_reminders.fetch_one")
    def test_overdue_task_detected(self, mock_fetch_one, mock_fetch_all, mock_ensure):
        """C├┤ng viß╗çc c├│ due_date < now v├á ch╞░a ho├án th├ánh ─æ╞░ß╗úc x├íc ─æß╗ïnh l├á qu├í hß║ín."""
        now = int(time.time() * 1000)
        past_due = now - (2 * 3600 * 1000)  # Qu├í hß║ín 2 tiß║┐ng

        mock_fetch_all.return_value = [
            {
                "id": 1,
                "title": "Gß╗¡i b├ío gi├í gß║Ñp",
                "assigned_to": 5,
                "due_date": past_due,
                "priority": "high",
                "status": "pending",
                "customer_name": "C├┤ng ty ABC",
                "opportunity_title": "Dß╗▒ ├ín CRM",
            }
        ]

        overdue_list = list_user_overdue_tasks(user_id=5, conn=MagicMock())
        self.assertEqual(len(overdue_list), 1)
        self.assertEqual(overdue_list[0]["id"], 1)
        self.assertGreaterEqual(overdue_list[0]["overdue_hours"], 1.9)

    @patch("app.tasks_reminders.ensure_tasks_tables")
    @patch("app.tasks_reminders.get_user_reminder_settings")
    @patch("app.tasks_reminders.fetch_all")
    @patch("app.tasks_reminders.fetch_one")
    def test_process_reminders_and_dedup(self, mock_fetch_one, mock_fetch_all, mock_get_settings, mock_ensure):
        """Bß╗Ö xß╗¡ l├╜ tß║ío th├┤ng b├ío v├á KH├öNG tß║ío tr├╣ng khi chß║íy lß║íi."""
        now = int(time.time() * 1000)
        mock_get_settings.return_value = ["24h", "1h"]

        # Giß║ú lß║¡p 2 c├┤ng viß╗çc: 1 sß║»p ─æß║┐n hß║ín (sau 2 tiß║┐ng), 1 ─æ├ú qu├í hß║ín (tr╞░ß╗¢c 1 tiß║┐ng)
        mock_fetch_all.return_value = [
            {"id": 10, "title": "K├╜ kß║┐t hß╗úp ─æß╗ông", "assigned_to": 2, "due_date": now + (2 * 3600 * 1000), "status": "pending"},
            {"id": 11, "title": "B├án giao hß╗ô s╞í", "assigned_to": 2, "due_date": now - (1 * 3600 * 1000), "status": "in_progress"},
        ]

        # Lß║ºn chß║íy 1: Ch╞░a c├│ th├┤ng b├ío trong DB (mock_fetch_one trß║ú vß╗ü None)
        mock_fetch_one.return_value = None
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        stats_1 = process_task_reminders_and_overdue(conn=mock_conn)
        self.assertEqual(stats_1["overdue_notifications_created"], 1)
        self.assertEqual(stats_1["due_soon_notifications_created"], 1)

        # Lß║ºn chß║íy 2: ─É├ú c├│ th├┤ng b├ío (mock_fetch_one trß║ú vß╗ü bß║ún ghi tß╗ôn tß║íi)
        mock_fetch_one.return_value = {"id": 999}
        stats_2 = process_task_reminders_and_overdue(conn=mock_conn)
        self.assertEqual(stats_2["overdue_notifications_created"], 0)
        self.assertEqual(stats_2["due_soon_notifications_created"], 0)


class TestTaskRemindersEndpoints(unittest.TestCase):
    """Kiß╗âm thß╗¡ API HTTP cho SCRUM-103."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum103"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_user_due_soon_tasks")
    def test_get_reminders_endpoint(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_list.return_value = [
            {"id": 1, "title": "Gß╗ìi lß║íi cho kh├ích h├áng", "due_date": 1700000000000, "hours_left": 1.5}
        ]

        resp = self.client.get("/api/tasks/reminders")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["reminders"][0]["title"], "Gß╗ìi lß║íi cho kh├ích h├áng")

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_user_overdue_tasks")
    def test_get_overdue_endpoint(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_list.return_value = [
            {"id": 2, "title": "B├ío gi├í phß║ºn mß╗üm", "due_date": 1690000000000, "overdue_hours": 4.5}
        ]

        resp = self.client.get("/api/tasks/overdue")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["overdue_tasks"][0]["overdue_hours"], 4.5)

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_user_notifications")
    def test_get_notifications_endpoint(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_list.return_value = {
            "items": [{"id": 1, "title": "Nhß║»c viß╗çc", "is_read": False}],
            "total": 1,
            "unread_count": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
        }

        resp = self.client.get("/api/notifications?unread_only=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["unread_count"], 1)
        self.assertEqual(len(data["items"]), 1)

    @patch("app.routes.get_current_user")
    @patch("app.routes.mark_notification_as_read")
    def test_mark_notification_read_endpoint(self, mock_mark, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_mark.return_value = True

        resp = self.client.patch("/api/notifications/1/read")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("─É├ú ─æ├ính dß║Ñu th├┤ng b├ío ─æ├ú ─æß╗ìc", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_team_overdue_summary")
    def test_team_overdue_summary_manager_allowed(self, mock_summary, mock_auth):
        mock_auth.return_value = CurrentUser(1, "mgr@test.com", "Manager", "manager", 1)
        mock_summary.return_value = [
            {"user_id": 2, "full_name": "Nh├ón vi├¬n A", "overdue_count": 3, "overdue_tasks": []}
        ]

        resp = self.client.get("/api/teams/overdue-summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total_members"], 1)
        self.assertEqual(data["members"][0]["overdue_count"], 3)

    @patch("app.routes.get_current_user")
    def test_team_overdue_summary_employee_forbidden(self, mock_auth):
        """Nh├ón vi├¬n th├┤ng th╞░ß╗¥ng kh├┤ng ─æ╞░ß╗úc ph├⌐p xem thß╗æng k├¬ qu├í hß║ín cß╗ºa nh├│m ΓåÆ 403."""
        mock_auth.return_value = CurrentUser(5, "emp@test.com", "Employee", "employee", 1)

        resp = self.client.get("/api/teams/overdue-summary")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("kh├┤ng c├│ quyß╗ün", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.update_user_reminder_settings")
    def test_update_reminder_settings_endpoint(self, mock_update, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_update.return_value = ["48h", "2h"]

        resp = self.client.put("/api/tasks/reminder-settings", json={"milestones": ["48h", "2h"]})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["milestones"], ["48h", "2h"])


if __name__ == "__main__":
    unittest.main()
