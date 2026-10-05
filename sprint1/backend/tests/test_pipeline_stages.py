"""
tests/test_pipeline_stages.py — Automated Integration Tests for S2-09:
- Pipeline Stage Configuration & Win Probability
- Stage Exit Conditions Validation
- Weighted Sales Forecast Summary Calculation
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


class TestPipelineStagesAPI:
    def test_list_pipeline_stages(self, client):
        login_as(client, "manager@company.vn", "Manager@123")
        res = client.get("/api/pipeline-stages")
        assert res.status_code == 200
        data = res.get_json()
        assert "items" in data
        assert len(data["items"]) >= 5
        assert any(s["stage_key"] == "negotiation" for s in data["items"])

    def test_create_pipeline_stage_manager_permission(self, client):
        login_as(client, "manager@company.vn", "Manager@123")
        res = client.post(
            "/api/pipeline-stages",
            json={
                "stage_key": "contract_sent",
                "stage_name": "Đã gửi hợp đồng",
                "win_probability": 80,
                "display_order": 45,
                "required_conditions": {"min_meetings": 1},
            },
        )
        assert res.status_code in (201, 400)

    def test_forecast_summary_report(self, client):
        login_as(client, "manager@company.vn", "Manager@123")
        res = client.get("/api/forecast/summary")
        assert res.status_code == 200
        data = res.get_json()
        assert "summary_by_stage" in data
        assert "total_pipeline_value" in data
        assert "total_forecast_amount" in data
        assert data["total_pipeline_value"] >= 0
        assert data["total_forecast_amount"] >= 0

    def test_stage_exit_conditions_validation(self, client):
        login_as(client, "manager@company.vn", "Manager@123")

        # Get customer ID
        cust_res = client.get("/api/customers")
        cust_id = cust_res.get_json()["items"][0]["id"]

        # Stage 'needs_analysis' requires at least 1 meeting (min_meetings: 1)
        # Attempting to move to 'needs_analysis' with meetings_count = 0 should fail!
        res = client.post(
            "/api/opportunities",
            json={
                "title": "Cơ hội thử nghiệm chuyển giai đoạn",
                "customer_id": cust_id,
                "value": 100000000,
                "stage_key": "initial_contact",
                "meetings_count": 0,
                "custom_fields": {"lead_source": "Website"},
            },
        )

        assert res.status_code == 201
        opp_id = res.get_json()["opportunity"]["id"]

        # Attempt to update to 'needs_analysis' with 0 meetings -> FAIL
        update_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm chuyển giai đoạn",
                "customer_id": cust_id,
                "stage_key": "needs_analysis",
                "meetings_count": 0,
            },
        )
        assert update_res.status_code == 400
        assert "cuộc gặp" in update_res.get_json()["message"]

        # Update with meetings_count = 1 -> SUCCESS
        valid_res = client.put(
            f"/api/opportunities/{opp_id}",
            json={
                "title": "Cơ hội thử nghiệm chuyển giai đoạn",
                "customer_id": cust_id,
                "stage_key": "needs_analysis",
                "meetings_count": 1,
            },
        )
        assert valid_res.status_code == 200
        assert valid_res.get_json()["opportunity"]["stage_key"] == "needs_analysis"
