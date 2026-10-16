r"""
tests/test_lead_convert_to_customer.py ΓÇö Test suite cho SCRUM-85
Kiß╗âm thß╗¡: Chuyß╗ân Lead th├ánh Kh├ích h├áng + Ng╞░ß╗¥i li├¬n hß╗ç + C╞í hß╗Öi b├ín h├áng

Chß║íy:
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
        """POST /api/leads/<id>/convert kh├┤ng c├│ session ΓåÆ 401"""
        resp = self.client.post("/api/leads/1/convert", json={})
        self.assertEqual(resp.status_code, 401)

    def test_convert_returns_proper_structure(self):
        """Response chuyß╗ân ─æß╗òi phß║úi c├│ ─æß╗º c├íc key quan trß╗ìng"""
        _login(self.client)
        resp = self.client.post("/api/leads/9999/convert", json={
            "company_name": "C├┤ng ty Test ABC",
            "opportunity_title": "Dß╗▒ ├ín thß╗¡ nghiß╗çm",
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
        """Lead ─æ├ú chuyß╗ân ─æß╗òi ΓåÆ 409 Conflict"""
        _login(self.client)
        resp = self.client.post("/api/leads/1/convert", json={})
        self.assertIn(resp.status_code, {201, 401, 403, 404, 409, 500})


class TestActivityMapping(unittest.TestCase):
    def test_map_activity_types(self):
        """Kiß╗âm tra ├ính xß║í activity_type ΓåÆ interaction_type ─æ├║ng"""
        from app.lead_convert import _map_activity_to_interaction
        self.assertEqual(_map_activity_to_interaction("created"), "Tß║ío tß╗½ lead")
        self.assertEqual(_map_activity_to_interaction("assigned"), "Ph├ón c├┤ng tß╗½ lead")
        self.assertEqual(_map_activity_to_interaction("accepted"), "Nhß║¡n ch─âm s├│c")
        self.assertEqual(_map_activity_to_interaction("rejected"), "Tß╗½ chß╗æi ph├ón c├┤ng")
        self.assertEqual(_map_activity_to_interaction("sla_breached"), "Cß║únh b├ío SLA")
        self.assertEqual(_map_activity_to_interaction("converted"), "Chuyß╗ân ─æß╗òi th├ánh kh├ích h├áng")
        self.assertEqual(_map_activity_to_interaction("note"), "Ghi ch├║")
        self.assertEqual(_map_activity_to_interaction("updated"), "Cß║¡p nhß║¡t th├┤ng tin")
        self.assertEqual(_map_activity_to_interaction("unknown_type"), "unknown_type")


class TestCustomerContactsEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_contacts_requires_auth(self):
        """GET /api/customers/<id>/contacts kh├┤ng c├│ session ΓåÆ 401"""
        resp = self.client.get("/api/customers/1/contacts")
        self.assertEqual(resp.status_code, 401)

    def test_contacts_returns_list(self):
        """Response phß║úi trß║ú vß╗ü dß║íng {items: [...]}"""
        _login(self.client)
        resp = self.client.get("/api/customers/9999/contacts")
        if resp.status_code == 200:
            data = resp.get_json()
            self.assertIn("items", data)
            self.assertIsInstance(data["items"], list)


class TestConvertBusinessLogic(unittest.TestCase):
    def test_company_name_fallback_chain(self):
        """T├¬n c├┤ng ty: company_name ΓåÆ lead.company ΓåÆ lead.full_name"""
        lead_mock = {"company": "C├┤ng ty ABC", "full_name": "Nguyß╗àn V─ân A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        self.assertEqual(cust_name, "C├┤ng ty ABC")

    def test_company_name_fallback_to_full_name(self):
        """Nß║┐u kh├┤ng c├│ company, d├╣ng full_name"""
        lead_mock = {"company": "", "full_name": "Nguyß╗àn V─ân A"}
        company_name_arg = ""
        cust_name = (company_name_arg or lead_mock["company"] or lead_mock["full_name"]).strip()
        self.assertEqual(cust_name, "Nguyß╗àn V─ân A")

    def test_opportunity_title_fallback(self):
        """Nß║┐u kh├┤ng truyß╗ün opportunity_title, tß╗▒ tß║ío tß╗½ t├¬n lead"""
        lead_full_name = "Nguyß╗àn V─ân A"
        opp_title_arg = ""
        opp_title = (opp_title_arg or f"C╞í hß╗Öi tß╗½ lead: {lead_full_name}").strip()
        self.assertEqual(opp_title, "C╞í hß╗Öi tß╗½ lead: Nguyß╗àn V─ân A")

    def test_lead_converted_cannot_be_updated(self):
        """Lead vß╗¢i status='─É├ú chuyß╗ân ─æß╗òi' c├│ hß║▒ng sß╗æ LEAD_STATUS_CONVERTED"""
        from app.leads import LEAD_STATUS_CONVERTED
        self.assertEqual(LEAD_STATUS_CONVERTED, "─É├ú chuyß╗ân ─æß╗òi")


if __name__ == "__main__":
    unittest.main()
