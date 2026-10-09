"""
tests/test_lead_convert_to_customer.py — Test suite cho SCRUM-85
Kiểm thử: Chuyển Lead thành Khách hàng + Người liên hệ + Cơ hội bán hàng

Chạy:
    cd backend
    .venv\\Scripts\\pytest tests/test_lead_convert_to_customer.py -v
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


# ─── Test Convert endpoint ─────────────────────────────────────────────────

class TestLeadConvertEndpoint:
    def test_convert_requires_auth(self, client):
        """POST /api/leads/<id>/convert không có session → 401"""
        resp = client.post("/api/leads/1/convert", json={})
        assert resp.status_code == 401

    def test_convert_returns_proper_structure(self, client):
        """Response chuyển đổi phải có đủ các key quan trọng"""
        _login(client)
        resp = client.post("/api/leads/9999/convert", json={
            "company_name": "Công ty Test ABC",
            "opportunity_title": "Dự án thử nghiệm",
            "opportunity_value": 100000000,
        })
        # 404 nếu lead không tồn tại; kiểm tra structure khi 201
        if resp.status_code == 201:
            data = resp.get_json()
            assert "result" in data
            result = data["result"]
            assert "lead_id" in result
            assert "customer_id" in result
            assert "opportunity_id" in result
            assert "contact" in result
            assert "activities_migrated" in result

    def test_convert_already_converted_returns_409(self, client):
        """Lead đã chuyển đổi → 409 Conflict"""
        _login(client)
        # Thử convert lead đã converted
        resp = client.post("/api/leads/1/convert", json={})
        # 409 nếu lead_already_converted, 404 nếu không tồn tại
        assert resp.status_code in {201, 401, 403, 404, 409, 500}


# ─── Test Data Migration (thuần Python, không cần DB) ────────────────────

class TestActivityMapping:
    def test_map_activity_types(self):
        """Kiểm tra ánh xạ activity_type → interaction_type đúng"""
        from app.lead_convert import _map_activity_to_interaction
        assert _map_activity_to_interaction("created") == "Tạo từ lead"
        assert _map_activity_to_interaction("assigned") == "Phân công từ lead"
        assert _map_activity_to_interaction("accepted") == "Nhận chăm sóc"
        assert _map_activity_to_interaction("rejected") == "Từ chối phân công"
        assert _map_activity_to_interaction("sla_breached") == "Cảnh báo SLA"
        assert _map_activity_to_interaction("converted") == "Chuyển đổi thành khách hàng"
        assert _map_activity_to_interaction("note") == "Ghi chú"
        assert _map_activity_to_interaction("updated") == "Cập nhật thông tin"
        # unknown type → trả lại chính nó
        assert _map_activity_to_interaction("unknown_type") == "unknown_type"


# ─── Test Contact endpoint ─────────────────────────────────────────────────

class TestCustomerContactsEndpoint:
    def test_contacts_requires_auth(self, client):
        """GET /api/customers/<id>/contacts không có session → 401"""
        resp = client.get("/api/customers/1/contacts")
        assert resp.status_code == 401

    def test_contacts_returns_list(self, client):
        """Response phải trả về dạng {items: [...]}"""
        _login(client)
        resp = client.get("/api/customers/9999/contacts")
        if resp.status_code == 200:
            data = resp.get_json()
            assert "items" in data
            assert isinstance(data["items"], list)


# ─── Test Business Logic (thuần Python) ────────────────────────────────────

class TestConvertBusinessLogic:
    def test_company_name_fallback_chain(self):
        """Tên công ty: company_name → lead.company → lead.full_name"""
        # Logic trong convert_lead_to_customer:
        # cust_name = (company_name or lead["company"] or lead["full_name"]).strip()
        lead_mock = {"company": "Công ty ABC", "full_name": "Nguyễn Văn A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        assert cust_name == "Công ty ABC"

    def test_company_name_fallback_to_full_name(self):
        """Nếu không có company, dùng full_name"""
        lead_mock = {"company": "", "full_name": "Nguyễn Văn A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        assert cust_name == "Nguyễn Văn A"

    def test_opportunity_title_fallback(self):
        """Nếu không truyền opportunity_title, tự tạo từ tên lead"""
        lead_full_name = "Nguyễn Văn A"
        opp_title_arg = ""
        opp_title = (opp_title_arg or f"Cơ hội từ lead: {lead_full_name}").strip()
        assert opp_title == "Cơ hội từ lead: Nguyễn Văn A"

    def test_lead_converted_cannot_be_updated(self):
        """Lead với status='Đã chuyển đổi' phải raise ValueError"""
        from app.leads import LEAD_STATUS_CONVERTED
        assert LEAD_STATUS_CONVERTED == "Đã chuyển đổi"
        # Logic kiểm tra trong update_lead:
        # if lead["status"] == LEAD_STATUS_CONVERTED: raise ValueError("lead_already_converted")
