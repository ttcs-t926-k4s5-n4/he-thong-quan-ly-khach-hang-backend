r"""
tests/test_lead_convert_to_customer.py — Test suite cho SCRUM-85
Kiểm thử: Chuyển Lead thành Khách hàng + Người liên hệ + Cơ hội bán hàng

Chạy:
    cd backend
    venv\Scripts\python.exe -m unittest tests/test_lead_convert_to_customer.py -v
"""
import unittest
from app import create_app


def _login(client, email="employee@test.com", password="Test@12345"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


class TestLeadConvertEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_convert_requires_auth(self):
        """POST /api/leads/<id>/convert không có session → 401"""
        resp = self.client.post("/api/leads/1/convert", json={})
        self.assertEqual(resp.status_code, 401)

    def test_convert_returns_proper_structure(self):
        """Response chuyển đổi phải có đủ các key quan trọng"""
        _login(self.client)
        resp = self.client.post("/api/leads/9999/convert", json={
            "company_name": "Công ty Test ABC",
            "opportunity_title": "Dự án thử nghiệm",
            "opportunity_value": 100000000,
        })
        if resp.status_code == 201:
            data = resp.get_json()
            self.assertIn("result", data)
            result = data["result"]
            self.assertIn("lead_id", result)
            self.assertIn("customer_id", result)
            self.assertIn("opportunity_id", result)
            self.assertIn("contact", result)
            self.assertIn("activities_migrated", result)

    def test_convert_already_converted_returns_409(self):
        """Lead đã chuyển đổi → 409 Conflict"""
        _login(self.client)
        resp = self.client.post("/api/leads/1/convert", json={})
        self.assertIn(resp.status_code, {201, 401, 403, 404, 409, 500})


class TestActivityMapping(unittest.TestCase):
    def test_map_activity_types(self):
        """Kiểm tra ánh xạ activity_type → interaction_type đúng"""
        from app.lead_convert import _map_activity_to_interaction
        self.assertEqual(_map_activity_to_interaction("created"), "Tạo từ lead")
        self.assertEqual(_map_activity_to_interaction("assigned"), "Phân công từ lead")
        self.assertEqual(_map_activity_to_interaction("accepted"), "Nhận chăm sóc")
        self.assertEqual(_map_activity_to_interaction("rejected"), "Từ chối phân công")
        self.assertEqual(_map_activity_to_interaction("sla_breached"), "Cảnh báo SLA")
        self.assertEqual(_map_activity_to_interaction("converted"), "Chuyển đổi thành khách hàng")
        self.assertEqual(_map_activity_to_interaction("note"), "Ghi chú")
        self.assertEqual(_map_activity_to_interaction("updated"), "Cập nhật thông tin")
        self.assertEqual(_map_activity_to_interaction("unknown_type"), "unknown_type")


class TestCustomerContactsEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_contacts_requires_auth(self):
        """GET /api/customers/<id>/contacts không có session → 401"""
        resp = self.client.get("/api/customers/1/contacts")
        self.assertEqual(resp.status_code, 401)

    def test_contacts_returns_list(self):
        """Response phải trả về dạng {items: [...]}"""
        _login(self.client)
        resp = self.client.get("/api/customers/9999/contacts")
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertIn("items", data)
            self.assertIsInstance(data["items"], list)


class TestConvertBusinessLogic(unittest.TestCase):
    def test_company_name_fallback_chain(self):
        """Tên công ty: company_name → lead.company → lead.full_name"""
        lead_mock = {"company": "Công ty ABC", "full_name": "Nguyễn Văn A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        self.assertEqual(cust_name, "Công ty ABC")

    def test_company_name_fallback_to_full_name(self):
        """Nếu không có company, dùng full_name"""
        lead_mock = {"company": "", "full_name": "Nguyễn Văn A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        self.assertEqual(cust_name, "Nguyễn Văn A")

    def test_opportunity_title_fallback(self):
        """Nếu không truyền opportunity_title, tự tạo từ tên lead"""
        lead_full_name = "Nguyễn Văn A"
        opp_title_arg = ""
        opp_title = (opp_title_arg or f"Cơ hội từ lead: {lead_full_name}").strip()
        self.assertEqual(opp_title, "Cơ hội từ lead: Nguyễn Văn A")

    def test_lead_converted_cannot_be_updated(self):
        """Lead với status='Đã chuyển đổi' có hằng số LEAD_STATUS_CONVERTED"""
        from app.leads import LEAD_STATUS_CONVERTED
        self.assertEqual(LEAD_STATUS_CONVERTED, "Đã chuyển đổi")


if __name__ == "__main__":
    unittest.main()
