"""
Bộ Kiểm Thử Tự Động (Unit Tests) cho User Story SCRUM-16 / SCRUM-30
Kiểm tra các tiêu chí chấp nhận:
1. Mục menu không thuộc quyền thì không hiển thị
2. Hiển thị tên, vai trò và nhóm kinh doanh đang thuộc về
3. Bảo vệ an toàn route backend
"""

import unittest
import sys
import os

# Thêm thư mục gốc vào đường dẫn hệ thống để import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, USERS_DATABASE, ALL_MENU_ITEMS, get_user_menu


class TestRBACNavigationSystem(unittest.TestCase):

    def setUp(self):
        """Khởi tạo test client của Flask."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # ========================================================
    # TIÊU CHÍ 1: MỤC MENU KHÔNG THUỘC QUYỀN THÌ KHÔNG HIỂN THỊ
    # ========================================================
    def test_admin_has_full_menu(self):
        """Kiểm tra Giám đốc / Admin có đầy đủ 7/7 mục menu."""
        admin_user = USERS_DATABASE["admin"]
        menu = get_user_menu(admin_user)
        self.assertEqual(len(menu), 7)
        menu_ids = [m["id"] for m in menu]
        self.assertIn("dashboard", menu_ids)
        self.assertIn("customers", menu_ids)
        self.assertIn("deals", menu_ids)
        self.assertIn("team_reports", menu_ids)
        self.assertIn("team_targets", menu_ids)
        self.assertIn("user_management", menu_ids)
        self.assertIn("system_settings", menu_ids)

    def test_manager_has_restricted_menu(self):
        """Kiểm tra Trưởng nhóm chỉ thấy 5 mục, KHÔNG thấy 'user_management' và 'system_settings'."""
        manager_user = USERS_DATABASE["manager"]
        menu = get_user_menu(manager_user)
        self.assertEqual(len(menu), 5)
        menu_ids = [m["id"] for m in menu]
        self.assertIn("team_reports", menu_ids)
        self.assertIn("team_targets", menu_ids)
        # Các mục không thuộc quyền phải hoàn toàn không xuất hiện
        self.assertNotIn("user_management", menu_ids)
        self.assertNotIn("system_settings", menu_ids)

    def test_sales_rep_has_basic_menu(self):
        """Kiểm tra Chuyên viên chỉ thấy 3 mục, KHÔNG thấy các mục của Trưởng nhóm & Admin."""
        sales_user = USERS_DATABASE["sales"]
        menu = get_user_menu(sales_user)
        self.assertEqual(len(menu), 3)
        menu_ids = [m["id"] for m in menu]
        self.assertIn("dashboard", menu_ids)
        self.assertIn("customers", menu_ids)
        self.assertIn("deals", menu_ids)
        self.assertNotIn("team_reports", menu_ids)
        self.assertNotIn("team_targets", menu_ids)
        self.assertNotIn("user_management", menu_ids)
        self.assertNotIn("system_settings", menu_ids)

    def test_intern_has_only_dashboard(self):
        """Kiểm tra Thực tập sinh chỉ thấy duy nhất 1 mục Dashboard."""
        intern_user = USERS_DATABASE["intern"]
        menu = get_user_menu(intern_user)
        self.assertEqual(len(menu), 1)
        self.assertEqual(menu[0]["id"], "dashboard")

    # ========================================================
    # TIÊU CHÍ 2: HIỂN THỊ TÊN, VAI TRÒ VÀ NHÓM KINH DOANH
    # ========================================================
    def test_user_profile_information_complete(self):
        """Kiểm tra toàn bộ tài khoản đều có đầy đủ Tên, Vai trò, Nhóm kinh doanh."""
        for username, user in USERS_DATABASE.items():
            self.assertTrue(user["full_name"], f"{username} thiếu full_name")
            self.assertTrue(user["role_name"], f"{username} thiếu role_name")
            self.assertTrue(user["business_team"], f"{username} thiếu business_team")

    def test_rendered_html_contains_user_profile(self):
        """Kiểm tra trang web sau khi render có chứa đúng Tên, Vai trò và Nhóm kinh doanh."""
        with self.client:
            # Chuyển sang tài khoản sales
            self.client.get('/switch-user/sales', follow_redirects=True)
            res = self.client.get('/dashboard')
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')

            # Kiểm tra hiển thị Tên, Vai trò, Nhóm kinh doanh
            self.assertIn("Lê Hoàng Phúc", html)
            self.assertIn("Chuyên viên kinh doanh", html)
            self.assertIn("Nhóm Bán Lẻ Khu Vực Miền Bắc", html)

            # Kiểm tra Tiêu chí 1 trong HTML: Không render link quản lý nhân viên và cấu hình
            self.assertNotIn('href="/users"', html)
            self.assertNotIn('href="/settings"', html)

    # ========================================================
    # BẢO VỆ ROUTE BACKEND: TRUY CẬP TRỰC TIẾP URL BỊ CHẶN
    # ========================================================
    def test_direct_url_access_denied_for_unauthorized_user(self):
        """Nếu chuyên viên cố tình gõ link /users hoặc /settings thì backend sẽ chặn và báo lỗi."""
        with self.client:
            self.client.get('/switch-user/sales', follow_redirects=True)
            res = self.client.get('/users', follow_redirects=True)
            # Phải bị redirect về dashboard kèm thông báo lỗi flash
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')
            self.assertIn("Truy cập bị từ chối", html)


if __name__ == '__main__':
    unittest.main()
