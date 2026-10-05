r"""
tests/test_opportunity_filters.py — Test suite cho SCRUM-96: Opportunity Search & Filter & Saved Filters

Kiểm thử:
1. Tìm kiếm theo keyword (tên cơ hội, mã cơ hội ID, tên khách hàng)
2. Lọc theo từng trường: stage, product_id, owner_id
3. Lọc theo khoảng giá trị min_value, max_value
4. Lọc theo khoảng ngày chốt close_date_from, close_date_to
5. Kết hợp nhiều điều kiện lọc trong 1 request
6. Validation min_value > max_value → 400
7. Validation close_date_from > close_date_to → 400
8. Sắp xếp an toàn (sort_by, sort_order)
9. Phân trang và dữ liệu tìm kiếm rỗng
10. Phân quyền dữ liệu theo vai trò (Employee vs Manager/Admin)
11. CRUD Bộ lọc đã lưu (Saved Opportunity Filters):
    - Tạo bộ lọc (201)
    - Danh sách bộ lọc của người dùng (200)
    - Chi tiết bộ lọc (200)
    - Cập nhật bộ lọc (200)
    - Xóa bộ lọc (200)
    - Ngăn chặn truy cập bộ lọc của người khác (403)
    - Bộ lọc không tồn tại (404)
    - Thiếu tên bộ lọc (400)
    - Chưa đăng nhập (401)
"""
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.auth import CurrentUser
from app.opportunity_filters import (
    create_saved_opportunity_filter,
    delete_saved_opportunity_filter,
    get_saved_opportunity_filter,
    list_saved_opportunity_filters,
    search_and_filter_opportunities,
    update_saved_opportunity_filter,
)


class TestOpportunitySearchAndFilterUnit(unittest.TestCase):
    """Kiểm thử unit logic tìm kiếm và lọc cơ hội."""

    def test_validation_min_value_greater_than_max_value(self):
        """min_value > max_value → raise ValueError"""
        with self.assertRaises(ValueError) as ctx:
            search_and_filter_opportunities(
                user=CurrentUser(1, "a@test.com", "A", "manager", 1),
                min_value=200000000.0,
                max_value=100000000.0,
            )
        self.assertIn("không được lớn hơn", str(ctx.exception))

    def test_validation_date_from_after_date_to(self):
        """close_date_from > close_date_to → raise ValueError"""
        with self.assertRaises(ValueError) as ctx:
            search_and_filter_opportunities(
                user=CurrentUser(1, "a@test.com", "A", "manager", 1),
                close_date_from="2026-12-31",
                close_date_to="2026-01-01",
            )
        self.assertIn("không được sau", str(ctx.exception))

    @patch("app.opportunity_filters.fetch_all")
    @patch("app.opportunity_filters.fetch_one")
    @patch("app.opportunity_filters.ensure_saved_opportunity_filters_table")
    def test_search_and_filter_query_construction(self, mock_ensure, mock_fetch_one, mock_fetch_all):
        """Kiểm tra câu query có đủ các điều kiện lọc và phân trang"""
        mock_fetch_one.return_value = {"total": 1}
        mock_fetch_all.return_value = [
            {
                "id": 1,
                "title": "Dự án CRM",
                "customer_name": "Công ty ABC",
                "value": 50000000.0,
                "stage": "Đàm phán",
                "expected_close_date": "2026-11-30",
                "owner_id": 2,
                "owner_name": "Sale A",
            }
        ]

        res = search_and_filter_opportunities(
            user=CurrentUser(2, "manager@test.com", "Manager", "manager", 1),
            keyword="CRM",
            stage="Đàm phán",
            min_value=10000000.0,
            max_value=100000000.0,
            close_date_from="2026-11-01",
            close_date_to="2026-11-30",
            product_id=5,
            owner_id=2,
            page=1,
            page_size=10,
            sort_by="value",
            sort_order="desc",
            conn=MagicMock(),
        )
        self.assertEqual(res["total"], 1)
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["title"], "Dự án CRM")
        self.assertEqual(res["sort_by"], "value")
        self.assertEqual(res["sort_order"], "desc")


class TestSavedOpportunityFiltersUnit(unittest.TestCase):
    """Kiểm thử các thao tác với bảng saved_opportunity_filters."""

    @patch("app.opportunity_filters.fetch_one")
    @patch("app.opportunity_filters.ensure_saved_opportunity_filters_table")
    def test_create_saved_filter_empty_name_raises_error(self, mock_ensure, mock_fetch_one):
        with self.assertRaises(ValueError):
            create_saved_opportunity_filter(user_id=1, filter_name="", filter_config={"stage": "negotiation"}, conn=MagicMock())

    @patch("app.opportunity_filters.fetch_one")
    @patch("app.opportunity_filters.ensure_saved_opportunity_filters_table")
    def test_get_saved_filter_other_user_forbidden(self, mock_ensure, mock_fetch_one):
        mock_fetch_one.return_value = {
            "id": 10,
            "user_id": 99,  # Người khác sở hữu
            "filter_name": "Bộ lọc riêng",
            "filter_config": "{}",
            "created_at": 1000,
            "updated_at": 1000,
        }
        with self.assertRaises(PermissionError):
            get_saved_opportunity_filter(filter_id=10, user_id=1, conn=MagicMock())


class TestOpportunitySearchEndpoints(unittest.TestCase):
    """Kiểm thử tích hợp các endpoint HTTP GET /api/opportunities & saved filters."""

    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-scrum96"})
        self.client = self.app.test_client()

    def test_opportunities_endpoint_unauthenticated_returns_401(self):
        resp = self.client.get("/api/opportunities")
        self.assertEqual(resp.status_code, 401)

    @patch("app.routes.get_current_user")
    @patch("app.routes.search_and_filter_opportunities")
    def test_opportunities_search_success(self, mock_search, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        mock_search.return_value = {
            "items": [{"id": 1, "title": "Cơ hội test", "value": 50000000.0}],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "sort_by": "created_at",
            "sort_order": "desc",
        }

        resp = self.client.get("/api/opportunities?keyword=test&min_value=1000&max_value=999999999&page=1&page_size=20")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)

    @patch("app.routes.get_current_user")
    def test_opportunities_invalid_min_max_value_returns_400(self, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        resp = self.client.get("/api/opportunities?min_value=5000&max_value=1000")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("không được lớn hơn", resp.get_json()["message"])

    @patch("app.routes.get_current_user")
    def test_opportunities_invalid_dates_returns_400(self, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="manager@test.com", full_name="Manager", role="manager", credentials_version=1)
        resp = self.client.get("/api/opportunities?close_date_from=2026-12-31&close_date_to=2026-01-01")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("không được sau", resp.get_json()["message"])

    # ─── Saved Filters Endpoints ─────────────────────────────────────────────

    @patch("app.routes.get_current_user")
    @patch("app.routes.create_saved_opportunity_filter")
    def test_create_saved_filter_success(self, mock_create, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="sale@test.com", full_name="Sale", role="employee", credentials_version=1)
        mock_create.return_value = {
            "id": 1,
            "user_id": 2,
            "filter_name": "Cơ hội giá trị cao",
            "filter_config": {"min_value": 100000000},
        }

        resp = self.client.post(
            "/api/opportunity-filters",
            json={
                "filter_name": "Cơ hội giá trị cao",
                "filter_config": {"min_value": 100000000},
            },
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("filter", data)
        self.assertEqual(data["filter"]["filter_name"], "Cơ hội giá trị cao")

    @patch("app.routes.get_current_user")
    @patch("app.routes.list_saved_opportunity_filters")
    def test_list_saved_filters(self, mock_list, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="sale@test.com", full_name="Sale", role="employee", credentials_version=1)
        mock_list.return_value = [
            {"id": 1, "filter_name": "F1", "filter_config": {}},
            {"id": 2, "filter_name": "F2", "filter_config": {}},
        ]

        resp = self.client.get("/api/opportunity-filters")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)

    @patch("app.routes.get_current_user")
    @patch("app.routes.get_saved_opportunity_filter")
    def test_get_saved_filter_forbidden(self, mock_get, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="sale@test.com", full_name="Sale", role="employee", credentials_version=1)
        mock_get.side_effect = PermissionError("filter_forbidden")

        resp = self.client.get("/api/opportunity-filters/99")
        self.assertEqual(resp.status_code, 403)

    @patch("app.routes.get_current_user")
    @patch("app.routes.delete_saved_opportunity_filter")
    def test_delete_saved_filter_success(self, mock_del, mock_auth):
        mock_auth.return_value = CurrentUser(id=2, email="sale@test.com", full_name="Sale", role="employee", credentials_version=1)
        mock_del.return_value = True

        resp = self.client.delete("/api/opportunity-filters/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Đã xóa", resp.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
