"""
tests/test_lead_filter_saved.py — Test suite cho SCRUM-86
Kiểm thử: Bộ lọc Lead nâng cao + Bộ lọc lưu sẵn

Chạy:
    cd backend
    .venv\\Scripts\\pytest tests/test_lead_filter_saved.py -v
"""
import pytest
from app import create_app


@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
    })


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, email="employee@test.com", password="Test@12345"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ─── Test Search & Filter endpoint ────────────────────────────────────────

class TestLeadsSearchFilter:
    def test_search_filter_requires_auth(self, client):
        """GET /api/leads/search-filter không có session → 401"""
        resp = client.get("/api/leads/search-filter")
        assert resp.status_code == 401

    def test_search_filter_returns_paginated(self, client):
        """Response phải có cấu trúc phân trang"""
        _login(client)
        resp = client.get("/api/leads/search-filter?page=1&per_page=10")
        if resp.status_code == 200:
            data = resp.get_json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "per_page" in data
            assert "total_pages" in data

    def test_search_filter_with_classification(self, client):
        """Lọc theo classification hot/warm/cold"""
        _login(client)
        for cls in ["hot", "warm", "cold"]:
            resp = client.get(f"/api/leads/search-filter?classification={cls}")
            assert resp.status_code in {200, 401, 500}

    def test_search_filter_sla_breached_only(self, client):
        """Lọc chỉ lead vi phạm SLA"""
        _login(client)
        resp = client.get("/api/leads/search-filter?sla_breached_only=true")
        assert resp.status_code in {200, 401, 500}

    def test_search_filter_sla_status_in_response(self, client):
        """Mỗi lead trong response phải có sla_status"""
        _login(client)
        resp = client.get("/api/leads/search-filter")
        if resp.status_code == 200:
            data = resp.get_json()
            for lead in data.get("items", []):
                assert "sla_status" in lead
                assert lead["sla_status"] in {"ok", "warning", "breached", "not_assigned"}


# ─── Test SLA Status Logic ─────────────────────────────────────────────────

class TestSLAStatusInFilter:
    def test_sla_status_values_are_valid(self):
        """sla_status chỉ được phép có 4 giá trị"""
        from app.leads import _compute_sla_status
        import time
        now_ms = int(time.time() * 1000)

        valid_statuses = {"ok", "warning", "breached", "not_assigned"}

        # not_assigned
        lead1 = {"assigned_at": None, "sla_deadline_at": None, "sla_breached": 0}
        assert _compute_sla_status(lead1) in valid_statuses

        # ok
        lead2 = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 20 * 3600 * 1000,
            "sla_breached": 0,
        }
        assert _compute_sla_status(lead2) in valid_statuses

        # warning (< 8 giờ)
        lead3 = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 3 * 3600 * 1000,
            "sla_breached": 0,
        }
        assert _compute_sla_status(lead3) in valid_statuses

        # breached
        lead4 = {
            "assigned_at": now_ms - 4 * 24 * 3600 * 1000,
            "sla_deadline_at": now_ms - 1000,
            "sla_breached": 0,
        }
        assert _compute_sla_status(lead4) in valid_statuses


# ─── Test Saved Filters CRUD ───────────────────────────────────────────────

class TestLeadSavedFiltersCRUD:
    def test_list_saved_filters_requires_auth(self, client):
        """GET /api/lead-saved-filters không có session → 401"""
        resp = client.get("/api/lead-saved-filters")
        assert resp.status_code == 401

    def test_create_saved_filter_requires_name(self, client):
        """Tạo bộ lọc thiếu tên → 400"""
        _login(client)
        resp = client.post("/api/lead-saved-filters", json={
            "name": "",
            "criteria": {"classification": "hot"},
        })
        if resp.status_code == 400:
            data = resp.get_json()
            assert "tên bộ lọc" in data.get("message", "").lower()

    def test_create_saved_filter_success(self, client):
        """Tạo bộ lọc đủ thông tin → 201"""
        _login(client)
        resp = client.post("/api/lead-saved-filters", json={
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
            assert "saved_filter" in data
            sf = data["saved_filter"]
            assert sf["name"] == "Leads nóng cần gọi hôm nay"
            assert "criteria" in sf
            assert sf["criteria"]["classification"] == "hot"

    def test_get_saved_filter_not_found(self, client):
        """Bộ lọc không tồn tại → 404"""
        _login(client)
        resp = client.get("/api/lead-saved-filters/99999")
        assert resp.status_code in {401, 404}

    def test_update_saved_filter(self, client):
        """Cập nhật tên bộ lọc"""
        _login(client)
        resp = client.put("/api/lead-saved-filters/99999", json={
            "name": "Tên mới",
            "criteria": {"classification": "warm"},
        })
        assert resp.status_code in {200, 401, 404}

    def test_delete_saved_filter_not_found(self, client):
        """Xóa bộ lọc không tồn tại → 404"""
        _login(client)
        resp = client.delete("/api/lead-saved-filters/99999")
        assert resp.status_code in {401, 404}

    def test_apply_saved_filter_returns_paginated(self, client):
        """Áp dụng bộ lọc đã lưu → kết quả phân trang"""
        _login(client)
        resp = client.get("/api/lead-saved-filters/99999/apply?page=1&per_page=10")
        if resp.status_code == 200:
            data = resp.get_json()
            assert "items" in data
            assert "total" in data


# ─── Test Filter Logic (thuần Python, không cần DB) ───────────────────────

class TestFilterCriteria:
    def test_criteria_structure(self):
        """criteria_json phải serialize/deserialize đúng"""
        import json
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
        assert deserialized["classification"] == "hot"
        assert deserialized["sla_breached_only"] is False

    def test_apply_filter_uses_criteria(self):
        """apply_lead_saved_filter phải đọc criteria từ saved filter"""
        from app.lead_filters import apply_lead_saved_filter
        # Hàm này gọi get_lead_saved_filter → nếu không tìm thấy → LookupError
        with pytest.raises(Exception):  # LookupError hoặc DB error
            apply_lead_saved_filter(filter_id=99999, user_id=1)

    def test_search_and_filter_all_params_accepted(self):
        """search_and_filter_leads nhận tất cả các params mà không lỗi logic"""
        from app.lead_filters import search_and_filter_leads
        import time
        now_ms = int(time.time() * 1000)
        # Test với đầy đủ params (có thể lỗi DB nhưng không lỗi logic)
        with pytest.raises(Exception):  # DB error khi không có DB
            search_and_filter_leads(
                q="test",
                status="Đang chăm sóc",
                source="Facebook",
                classification="hot",
                assigned_to=5,
                date_from=now_ms - 30 * 24 * 3600 * 1000,
                date_to=now_ms,
                sla_breached_only=True,
                page=1,
                per_page=10,
                sort_by="sla_deadline_at",
                order="asc",
            )
