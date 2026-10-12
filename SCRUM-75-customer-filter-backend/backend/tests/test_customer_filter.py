"""
tests/test_customer_filter.py ΓÇö Automated Integration Tests for SCRUM-75:
- Multi-criteria Customer Filter (Status, Industry, Scale, Region, Owner)
- Multi-field Search (Name, Tax Code, Phone)
- Saved Filters CRUD
"""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def login_as(client, email="employee@company.vn", password="Employee@123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp


class TestCustomerFilterAPI:
    def test_search_and_filter_customers(self, client):
        login_as(client)

        # 1. Search by name keyword
        res = client.get("/api/customers/search-filter?q=Alpha")
        assert res.status_code == 200
        data = res.get_json()
        assert "items" in data
        assert data["total"] >= 1
        assert "Alpha" in data["items"][0]["name"]

        # 2. Filter by status
        res = client.get("/api/customers/search-filter?status=Tiß╗üm%20n─âng")
        assert res.status_code == 200
        data = res.get_json()
        assert all(c["status"] == "Tiß╗üm n─âng" for c in data["items"])

        # 3. Filter by custom field 'industry' = 'C├┤ng nghß╗ç'
        res = client.get("/api/customers/search-filter?industry=C├┤ng%20nghß╗ç")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["items"]) >= 1

    def test_saved_filters_crud(self, client):
        login_as(client)

        # 1. Create a new saved filter
        res = client.post(
            "/api/saved-filters",
            json={
                "name": "Kh├ích C├┤ng Nghß╗ç Tiß╗üm N─âng",
                "filter_target": "customer",
                "criteria": {"status": "Tiß╗üm n─âng", "industry": "C├┤ng nghß╗ç"},
            },
        )
        assert res.status_code == 201
        created = res.get_json()["saved_filter"]
        fid = created["id"]
        assert created["name"] == "Kh├ích C├┤ng Nghß╗ç Tiß╗üm N─âng"
        assert created["criteria"]["industry"] == "C├┤ng nghß╗ç"

        # 2. List saved filters
        res = client.get("/api/saved-filters?target=customer")
        assert res.status_code == 200
        items = res.get_json()["items"]
        assert any(f["id"] == fid for f in items)

        # 3. Update saved filter
        res = client.put(
            f"/api/saved-filters/{fid}",
            json={
                "name": "Kh├ích C├┤ng Nghß╗ç & B─ÉS Tiß╗üm N─âng",
                "criteria": {"status": "Tiß╗üm n─âng", "industry": "C├┤ng nghß╗ç, Bß║Ñt ─æß╗Öng sß║ún"},
            },
        )
        assert res.status_code == 200
        updated = res.get_json()["saved_filter"]
        assert updated["name"] == "Kh├ích C├┤ng Nghß╗ç & B─ÉS Tiß╗üm N─âng"

        # 4. Delete saved filter
        res = client.delete(f"/api/saved-filters/{fid}")
        assert res.status_code == 200

        # Verify deletion
        res = client.get(f"/api/saved-filters/{fid}")
        assert res.status_code == 404
