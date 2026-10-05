"""
tests/test_win_loss_reasons.py — Automated Integration Tests for S2-10:
- Win/Loss Reasons Directory Management
- Competitors Directory Management
- Mandatory Validation When Closing Opportunity (Won/Lost Constraint)
"""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def login_as(client, email="manager@company.vn", password="Manager@123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp


class TestWinLossReasonsAPI:
    def test_list_win_loss_reasons(self, client):
        login_as(client, "manager@company.vn", "Manager@123")
        res = client.get("/api/win-loss-reasons?type=win")
        assert res.status_code == 200
        items = res.get_json()["items"]
        assert len(items) >= 1
        assert all(item["reason_type"] == "win" for item in items)

    def test_list_competitors(self, client):
        login_as(client, "manager@company.vn", "Manager@123")
        res = client.get("/api/competitors")
        assert res.status_code == 200
        items = res.get_json()["items"]
        assert len(items) >= 1
        assert any(item["code"] == "comp_viet_sales" for item in items)

    def test_close_opportunity_won_validation(self, client):
        login_as(client, "manager@company.vn", "Manager@123")

        cust_id = client.get("/api/customers").get_json()["items"][0]["id"]
        win_reason_id = client.get("/api/win-loss-reasons?type=win").get_json()["items"][0]["id"]

        # Create opportunity
        res = client.post(
            "/api/opportunities",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thành công",
                "customer_id": cust_id,
                "value": 200000000,
                "stage_key": "negotiation",
                "meetings_count": 2,
                "custom_fields": {"lead_source": "Website"},
            },
        )
        assert res.status_code == 201
        opp_id = res.get_json()["opportunity"]["id"]

        # Attempting to move to 'closed_won' without win_reason_id -> FAIL
        fail_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thành công",
                "customer_id": cust_id,
                "stage_key": "closed_won",
            },
        )
        assert fail_res.status_code == 400
        assert "Lý do Thắng" in fail_res.get_json()["message"]

        # Closing with win_reason_id -> SUCCESS
        success_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thành công",
                "customer_id": cust_id,
                "stage_key": "closed_won",
                "win_reason_id": win_reason_id,
            },
        )
        assert success_res.status_code == 200
        opp_data = success_res.get_json()["opportunity"]
        assert opp_data["stage_key"] == "closed_won"
        assert opp_data["win_reason_id"] == win_reason_id

    def test_close_opportunity_lost_validation(self, client):
        login_as(client, "manager@company.vn", "Manager@123")

        cust_id = client.get("/api/customers").get_json()["items"][0]["id"]
        loss_reason_id = client.get("/api/win-loss-reasons?type=loss").get_json()["items"][0]["id"]
        competitor_id = client.get("/api/competitors").get_json()["items"][0]["id"]

        # Create opportunity
        res = client.post(
            "/api/opportunities",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thất bại",
                "customer_id": cust_id,
                "value": 150000000,
                "stage_key": "negotiation",
                "meetings_count": 2,
                "custom_fields": {"lead_source": "Website"},
            },
        )

        opp_id = res.get_json()["opportunity"]["id"]

        # Attempt to move to 'closed_lost' without competitor_id -> FAIL
        fail_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thất bại",
                "customer_id": cust_id,
                "stage_key": "closed_lost",
                "loss_reason_id": loss_reason_id,
                # missing competitor_id!
            },
        )
        assert fail_res.status_code == 400
        assert "Đối thủ cạnh tranh" in fail_res.get_json()["message"]

        # Closing with loss_reason_id and competitor_id -> SUCCESS
        success_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm Chốt Thất bại",
                "customer_id": cust_id,
                "stage_key": "closed_lost",
                "loss_reason_id": loss_reason_id,
                "competitor_id": competitor_id,
            },
        )
        assert success_res.status_code == 200
        opp_data = success_res.get_json()["opportunity"]
        assert opp_data["stage_key"] == "closed_lost"
        assert opp_data["loss_reason_id"] == loss_reason_id
        assert opp_data["competitor_id"] == competitor_id
