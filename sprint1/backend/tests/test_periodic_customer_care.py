"""
tests/test_periodic_customer_care.py — Automated Integration Tests for SCRUM-77:
- List Customers needing Periodic Care (Inactive in N days, sorted by contract_value DESC)
- Record Interaction & Mark Contacted directly from list (auto updates last_interaction_at)
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


class TestPeriodicCustomerCareAPI:
    def test_periodic_care_list_and_mark_contacted(self, client):
        login_as(client)

        # 1. Get periodic care customers inactive for 0 days (all customers)
        res = client.get("/api/customers/periodic-care?days=0")
        assert res.status_code == 200
        data = res.get_json()
        assert "items" in data
        assert len(data["items"]) >= 1

        # Check sorting by contract_value DESC
        values = [c["contract_value"] for c in data["items"]]
        assert values == sorted(values, reverse=True)

        target_cust_id = data["items"][0]["id"]

        # 2. Mark contacted directly from list
        res_contact = client.post(
            f"/api/customers/{target_cust_id}/mark-contacted",
            json={"notes": "Đã trao đổi qua điện thoại về hợp đồng gia hạn năm tới."},
        )
        assert res_contact.status_code == 201
        resp_data = res_contact.get_json()
        assert "interaction" in resp_data
        assert resp_data["interaction"]["customer_id"] == target_cust_id

        # 3. Check customer interactions history
        res_hist = client.get(f"/api/customers/{target_cust_id}/interactions")
        assert res_hist.status_code == 200
        interactions = res_hist.get_json()["items"]
        assert len(interactions) >= 1
        assert "Đã trao đổi qua điện thoại" in interactions[0]["notes"]

        # 4. Query with 30 days threshold -> recently contacted customer is excluded
        res_30days = client.get("/api/customers/periodic-care?days=30")
        assert res_30days.status_code == 200
        items_30 = res_30days.get_json()["items"]
        assert not any(c["id"] == target_cust_id for c in items_30)
