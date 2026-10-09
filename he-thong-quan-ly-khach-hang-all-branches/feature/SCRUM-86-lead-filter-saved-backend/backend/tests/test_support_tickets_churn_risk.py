"""
tests/test_support_tickets_churn_risk.py — Automated Integration Tests for SCRUM-76:
- Support Tickets CRUD (Create, List, View, Update, Delete)
- Auto Churn-Risk Flagging Engine
- Customer 360 View & Churn-Risk Alerts
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


class TestSupportTicketsChurnRiskAPI:
    def test_create_ticket_and_auto_churn_risk(self, client):
        login_as(client)

        # 1. Create initial ticket for customer ID 1
        res = client.post(
            "/api/support-tickets",
            json={
                "customer_id": 1,
                "title": "Lỗi kết nối API thanh toán",
                "description": "Hệ thống báo lỗi 500 khi thanh toán trực tuyến",
                "priority": "high",
                "status": "open",
            },
        )
        assert res.status_code == 201
        t1 = res.get_json()["ticket"]
        t1_id = t1["id"]

        # Check Customer 360 - Initially 1 high ticket (not yet churn risk)
        res_360 = client.get("/api/customers/1/360")
        assert res_360.status_code == 200
        data_360 = res_360.get_json()
        assert data_360["pending_tickets_count"] >= 1

        # 2. Create urgent ticket -> should trigger auto churn risk flag!
        res_urgent = client.post(
            "/api/support-tickets",
            json={
                "customer_id": 1,
                "title": "Hệ thống sập không đăng nhập được",
                "priority": "urgent",
                "status": "open",
            },
        )
        assert res_urgent.status_code == 201
        t2_id = res_urgent.get_json()["ticket"]["id"]

        # Check Customer 360 - Now is_churn_risk must be True!
        res_360 = client.get("/api/customers/1/360")
        data_360 = res_360.get_json()
        assert data_360["is_churn_risk"] is True
        assert data_360["alert"] is not None
        assert "KHẨN CẤP" in data_360["alert"]["message"]

        # Check Churn-Risk Alerts List
        res_alerts = client.get("/api/churn-risk-alerts")
        assert res_alerts.status_code == 200
        alerts = res_alerts.get_json()["items"]
        assert any(a["id"] == 1 for a in alerts)

        # 3. Resolve urgent ticket -> auto clear risk
        client.put(f"/api/support-tickets/{t2_id}", json={"title": "Hệ thống sập", "priority": "urgent", "status": "resolved"})
        client.put(f"/api/support-tickets/{t1_id}", json={"title": "Lỗi kết nối API", "priority": "high", "status": "resolved"})

        res_360_cleared = client.get("/api/customers/1/360")
        assert res_360_cleared.get_json()["is_churn_risk"] is False

        # Cleanup
        client.delete(f"/api/support-tickets/{t1_id}")
        client.delete(f"/api/support-tickets/{t2_id}")
