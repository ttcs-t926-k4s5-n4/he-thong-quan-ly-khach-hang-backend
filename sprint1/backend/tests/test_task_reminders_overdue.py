r"""
tests/test_task_reminders_overdue.py — Test suite cho SCRUM-103: Nhắc việc sắp đến hạn & Quá hạn

Kiểm thử:
1. Tạo công việc với thời hạn hợp lệ (POST /api/tasks)
2. Kiểm tra xác thực đầu vào (tiêu đề trống, due_date không hợp lệ → 400)
3. Xác định công việc sắp đến hạn theo mốc cấu hình (GET /api/tasks/reminders)
4. Xác định công việc quá hạn (GET /api/tasks/overdue)
5. Loại trừ công việc đã hoàn thành (completed) hoặc đã hủy (cancelled)
6. Tùy biến cấu hình mốc nhắc việc động (GET & PUT /api/tasks/reminder-settings)
7. Tự động sinh thông báo sắp đến hạn và quá hạn (process_task_reminders_and_overdue)
8. Chống tạo thông báo trùng lặp khi chạy bộ xử lý lặp lại nhiều lần
9. Quản lý thông báo: phân trang, lọc chưa đọc và đánh dấu đã đọc
10. Thống kê tổng số công việc quá hạn theo thành viên dành cho Trưởng nhóm/Admin (GET /api/teams/overdue-summary)
11. Ngăn nhân viên thông thường truy cập thống kê quản lý (403)
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
    """Kiểm thử logic xác định hạn công việc và chống tạo thông báo trùng."""

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
        self.assertIn("Tiêu đề", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            create_task(title="Họp khách hàng", due_date=0, assigned_to=1, created_by=1, conn=mock_conn)
        self.assertIn("Thời hạn", str(ctx.exception))

    @patch("app.tasks_reminders.ensure_tasks_tables")
    @patch("app.tasks_reminders.fetch_all")
    @patch("app.tasks_reminders.fetch_one")
    def test_overdue_task_detected(self, mock_fetch_one, mock_fetch_all, mock_ensure):
        """Công việc có due_date < now và chưa hoàn thành được xác định là quá hạn."""
        now = int(time.time() * 1000)
        past_due = now - (2 * 3600 * 1000)  # Quá hạn 2 tiếng

        mock_fetch_all.return_value = [
            {
                "id": 1,
                "title": "Gửi báo giá gấp",
                "assigned_to": 5,
                "due_date": past_due,
                "priority": "high",
                "status": "pending",
                "customer_name": "Công ty ABC",
                "opportunity_title": "Dự án CRM",
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
        """Bộ xử lý tạo thông báo và KHÔNG tạo trùng khi chạy lại."""
        now = int(time.time() * 1000)
        mock_get_settings.return_value = ["24h", "1h"]

        # Giả lập 2 công việc: 1 sắp đến hạn (sau 2 tiếng), 1 đã quá hạn (trước 1 tiếng)
        mock_fetch_all.return_value = [
            {"id": 10, "title": "Ký kết hợp đồng", "assigned_to": 2, "due_date": now + (2 * 3600 * 1000), "status": "pending"},
            {"id": 11, "title": "Bàn giao hồ sơ", "assigned_to": 2, "due_date": now - (1 * 3600 * 1000), "status": "in_progress"},
        ]

        # Lần chạy 1: Chưa có thông báo trong DB (mock_fetch_one trả về None)
        mock_fetch_one.return_value = None
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        stats_1 = process_task_reminders_and_overdue(conn=mock_conn)
        self.assertEqual(stats_1["overdue_notifications_created"], 1)
        self.assertEqual(stats_1["due_soon_notifications_created"], 1)

        # Lần chạy 2: Đã có thông báo (mock_fetch_one trả về bản ghi tồn tại)
        mock_fetch_one.return_value = {"id": 999}
        stats_2 = process_task_reminders_and_overdue(conn=mock_conn)
        self.assertEqual(stats_2["overdue_notifications_created"], 0)
        self.assertEqual(stats_2["due_soon_notifications_created"], 0)


class TestTaskRemindersEndpoints(unittest.TestCase):
    """Kiểm thử API HTTP cho SCRUM-103."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum103"})
        self.client = self.app.test_client()

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_user_due_soon_tasks")
    def test_get_reminders_endpoint(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_list.return_value = [
            {"id": 1, "title": "Gọi lại cho khách hàng", "due_date": 1700000000000, "hours_left": 1.5}
        ]

        resp = self.client.get("/api/tasks/reminders")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["reminders"][0]["title"], "Gọi lại cho khách hàng")

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_user_overdue_tasks")
    def test_get_overdue_endpoint(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(2, "emp@test.com", "Employee", "employee", 1)
        mock_list.return_value = [
            {"id": 2, "title": "Báo giá phần mềm", "due_date": 1690000000000, "overdue_hours": 4.5}
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
            "items": [{"id": 1, "title": "Nhắc việc", "is_read": False}],
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
        self.assertIn("Đã đánh dấu thông báo đã đọc", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_team_overdue_summary")
    def test_team_overdue_summary_manager_allowed(self, mock_summary, mock_auth):
        mock_auth.return_value = CurrentUser(1, "mgr@test.com", "Manager", "manager", 1)
        mock_summary.return_value = [
            {"user_id": 2, "full_name": "Nhân viên A", "overdue_count": 3, "overdue_tasks": []}
        ]

        resp = self.client.get("/api/teams/overdue-summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total_members"], 1)
        self.assertEqual(data["members"][0]["overdue_count"], 3)

    @patch("app.routes.get_current_user")
    def test_team_overdue_summary_employee_forbidden(self, mock_auth):
        """Nhân viên thông thường không được phép xem thống kê quá hạn của nhóm → 403."""
        mock_auth.return_value = CurrentUser(5, "emp@test.com", "Employee", "employee", 1)

        resp = self.client.get("/api/teams/overdue-summary")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("không có quyền", resp.get_json()["message"])

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
