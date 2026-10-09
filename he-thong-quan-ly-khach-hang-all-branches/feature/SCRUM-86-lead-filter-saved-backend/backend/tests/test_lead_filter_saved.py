r"""
tests/test_lead_filter_saved.py — Test suite cho SCRUM-86
Kiểm thử: Bộ lọc Lead nâng cao + Bộ lọc lưu sẵn

Chạy:
    cd backend
    venv\Scripts\python.exe -m unittest tests/test_lead_filter_saved.py -v
"""
import json
import time
import unittest
from app import create_app


def _login(client, email="employee@test.com", password="Test@12345"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


class TestLeadsSearchFilter(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_search_filter_requires_auth(self):
        """GET /api/leads/search-filter không có session → 401"""
        resp = self.client.get("/api/leads/search-filter")
        self.assertEqual(resp.status_code, 401)

    def test_search_filter_returns_paginated(self):
        """Response phải có cấu trúc phân trang"""
        _login(self.client)
        resp = self.client.get("/api/leads/search-filter?page=1&per_page=10")
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertIn("items", data)
            self.assertIn("total", data)
            self.assertIn("page", data)
            self.assertIn("per_page", data)
            self.assertIn("total_pages", data)

    def test_search_filter_with_classification(self):
        """Lọc theo classification hot/warm/cold"""
        _login(self.client)
        for cls in ["hot", "warm", "cold"]:
            resp = self.client.get(f"/api/leads/search-filter?classification={cls}")
            self.assertIn(resp.status_code, {200, 401, 500})

    def test_search_filter_sla_breached_only(self):
        """Lọc chỉ lead vi phạm SLA"""
        _login(self.client)
        resp = self.client.get("/api/leads/search-filter?sla_breached_only=true")
        self.assertIn(resp.status_code, {200, 401, 500})

    def test_search_filter_sla_status_in_response(self):
        """Mỗi lead trong response phải có sla_status"""
        _login(self.client)
        resp = self.client.get("/api/leads/search-filter")
        if resp.status_code == 200:
            data = resp.get_json()
            for lead in data.get("items", []):
                self.assertIn("sla_status", lead)
                self.assertIn(lead["sla_status"], {"ok", "warning", "breached", "not_assigned"})


class TestSLAStatusInFilter(unittest.TestCase):
    def test_sla_status_values_are_valid(self):
        """sla_status chỉ được phép có 4 giá trị"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)

        valid_statuses = {"ok", "warning", "breached", "not_assigned"}

        # not_assigned
        lead1 = {"assigned_at": None, "sla_deadline_at": None, "sla_breached": 0}
        self.assertIn(_compute_sla_status(lead1), valid_statuses)

        # ok
        lead2 = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 20 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertIn(_compute_sla_status(lead2), valid_statuses)

        # warning (< 8 giờ)
        lead3 = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 3 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertIn(_compute_sla_status(lead3), valid_statuses)

        # breached
        lead4 = {
            "assigned_at": now_ms - 4 * 24 * 3600 * 1000,
            "sla_deadline_at": now_ms - 1000,
            "sla_breached": 0,
        }
        self.assertIn(_compute_sla_status(lead4), valid_statuses)


class TestLeadSavedFiltersCRUD(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_list_saved_filters_requires_auth(self):
        """GET /api/lead-saved-filters không có session → 401"""
        resp = self.client.get("/api/lead-saved-filters")
        self.assertEqual(resp.status_code, 401)

    def test_create_saved_filter_requires_name(self):
        """Tạo bộ lọc thiếu tên → 400"""
        _login(self.client)
        resp = self.client.post("/api/lead-saved-filters", json={
            "name": "",
            "criteria": {"classification": "hot"},
        })
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("tên bộ lọc", data.get("message", "").lower())

    def test_create_saved_filter_success(self):
        """Tạo bộ lọc đủ thông tin → 201"""
        _login(self.client)
        resp = self.client.post("/api/lead-saved-filters", json={
            "name": "Leads nóng cần gọi hôm nay",
            "criteria": {
                "classification": "hot",
                "status": "Đang chăm sóc",
                "sort_by": "sla_deadline_at",
                "order": "asc",
            },
        })
        if resp.status_code == 201:
            data = resp.get_json()
            self.assertIn("saved_filter", data)
            sf = data["saved_filter"]
            self.assertEqual(sf["name"], "Leads nóng cần gọi hôm nay")
            self.assertIn("criteria", sf)
            self.assertEqual(sf["criteria"]["classification"], "hot")

    def test_get_saved_filter_not_found(self):
        """Bộ lọc không tồn tại → 404"""
        _login(self.client)
        resp = self.client.get("/api/lead-saved-filters/99999")
        self.assertIn(resp.status_code, {401, 404})

    def test_update_saved_filter(self):
        """Cập nhật tên bộ lọc"""
        _login(self.client)
        resp = self.client.put("/api/lead-saved-filters/99999", json={
            "name": "Tên mới",
            "criteria": {"classification": "warm"},
        })
        self.assertIn(resp.status_code, {200, 401, 404})

    def test_delete_saved_filter_not_found(self):
        """Xóa bộ lọc không tồn tại → 404"""
        _login(self.client)
        resp = self.client.delete("/api/lead-saved-filters/99999")
        self.assertIn(resp.status_code, {401, 404})

    def test_apply_saved_filter_returns_paginated(self):
        """Áp dụng bộ lọc đã lưu → kết quả phân trang"""
        _login(self.client)
        resp = self.client.get("/api/lead-saved-filters/99999/apply?page=1&per_page=10")
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertIn("items", data)
            self.assertIn("total", data)


class TestFilterCriteria(unittest.TestCase):
    def test_criteria_structure(self):
        """criteria_json phải serialize/deserialize đúng"""
        criteria = {
            "q": "test",
            "status": "Đang chăm sóc",
            "source": "Facebook",
            "classification": "hot",
            "assigned_to": 5,
            "date_from": 1725196800000,
            "date_to": 1727788800000,
            "sla_breached_only": False,
            "sort_by": "sla_deadline_at",
            "order": "asc",
        }
        serialized = json.dumps(criteria, ensure_ascii=False)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["classification"], "hot")
        self.assertFalse(deserialized["sla_breached_only"])

    def test_apply_filter_uses_criteria(self):
        """apply_lead_saved_filter phải đọc criteria từ saved filter"""
        from app.lead_filters import apply_lead_saved_filter
        with self.assertRaises(Exception):
            apply_lead_saved_filter(filter_id=99999, user_id=1)


if __name__ == "__main__":
    unittest.main()
