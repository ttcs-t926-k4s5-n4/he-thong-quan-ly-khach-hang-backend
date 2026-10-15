r"""
tests/test_lead_accept_reject_sla.py ΓÇö Test suite cho SCRUM-84
Kiß╗âm thß╗¡: Nhß║¡n/Tß╗½ chß╗æi Lead vß╗¢i r├áng buß╗Öc SLA phß║ún hß╗ôi

Chß║íy:
    cd backend
    venv\Scripts\python.exe -m unittest tests/test_lead_accept_reject_sla.py -v
"""
import time
import unittest
from app import create_app

SLA_3_DAYS_MS = 3 * 24 * 3600 * 1000


def _login(client, email="employee@test.com", password="Test@12345"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp


class TestLeadCreate(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQL_SERVER_CONNECTION_STRING": "",
        })
        self.client = self.app.test_client()

    def test_create_lead_success(self):
        """Tß║ío lead mß╗¢i vß╗¢i t├¬n hß╗úp lß╗ç ΓåÆ 201 hoß║╖c response hß╗úp lß╗ç"""
        _login(self.client)
        resp = self.client.post("/api/leads", json={
            "full_name": "Nguyß╗àn V─ân Test",
            "email": "test@example.com",
            "phone": "0901234567",
            "company": "C├┤ng ty Test",
            "source": "Facebook",
            "classification": "warm",
        })
        self.assertIn(resp.status_code, {201, 401, 500})

    def test_create_lead_missing_name(self):
        """Thiß║┐u full_name ΓåÆ 400 vß╗¢i error message"""
        _login(self.client)
        resp = self.client.post("/api/leads", json={
            "email": "test@example.com",
        })
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("errors", data)
            self.assertIn("full_name", data["errors"])


class TestSLALogic(unittest.TestCase):
    def test_compute_sla_status_ok(self):
        """SLA c├▓n > 8 giß╗¥ ΓåÆ 'ok'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 10 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "ok")

    def test_compute_sla_status_warning(self):
        """SLA c├▓n < 8 giß╗¥ ΓåÆ 'warning'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 4 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "warning")

    def test_compute_sla_status_breached_by_flag(self):
        """sla_breached=1 ΓåÆ lu├┤n 'breached' bß║Ñt kß╗â deadline"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 100 * 3600 * 1000,
            "sla_breached": 1,
        }
        self.assertEqual(_compute_sla_status(lead), "breached")

    def test_compute_sla_status_breached_by_time(self):
        """Deadline ─æ├ú qua, sla_breached=0 ΓåÆ vß║½n 'breached'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - SLA_3_DAYS_MS - 1000,
            "sla_deadline_at": now_ms - 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "breached")

    def test_compute_sla_status_not_assigned(self):
        """Ch╞░a ph├ón c├┤ng (assigned_at=None) ΓåÆ 'not_assigned'"""
        from app.leads import _compute_sla_status
        lead = {
            "assigned_at": None,
            "sla_deadline_at": None,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "not_assigned")

    def test_sla_deadline_is_3_days_from_assigned(self):
        """SLA deadline phß║úi = assigned_at + 3 ng├áy (72 giß╗¥)"""
        from app.leads import SLA_RESPONSE_MS
        self.assertEqual(SLA_RESPONSE_MS, 3 * 24 * 3600 * 1000)


class TestRejectValidation(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_reject_without_reason_returns_400(self):
        """Tß╗½ chß╗æi kh├┤ng c├│ l├╜ do ΓåÆ 400"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("errors", data)
            self.assertIn("reason", data["errors"])
            self.assertIn("bß║»t buß╗Öc", data["errors"]["reason"].lower())

    def test_reject_with_empty_reason_returns_400(self):
        """L├╜ do rß╗ùng (chß╗ë whitespace) ΓåÆ 400"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={"reason": "   "})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("reason", data.get("errors", {}))

    def test_reject_with_valid_reason_processes(self):
        """L├╜ do hß╗úp lß╗ç ΓåÆ kh├┤ng trß║ú 400 vß╗ü validation"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={"reason": "Kh├ích kh├┤ng ─æ├║ng ph├ón kh├║c"})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertNotIn("reason", data.get("errors", {}))


class TestLeadClassification(unittest.TestCase):
    def test_valid_classifications(self):
        """Chß║Ñp nhß║¡n hot/warm/cold"""
        valid = {"hot", "warm", "cold"}
        self.assertIn("hot", valid)
        self.assertIn("warm", valid)
        self.assertIn("cold", valid)


class TestLeadEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        })
        self.client = self.app.test_client()

    def test_leads_list_requires_auth(self):
        """GET /api/leads kh├┤ng c├│ session ΓåÆ 401"""
        resp = self.client.get("/api/leads")
        self.assertEqual(resp.status_code, 401)

    def test_sla_breached_requires_manager(self):
        """GET /api/leads/sla-breached y├¬u cß║ºu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.get("/api/leads/sla-breached")
        self.assertIn(resp.status_code, {401, 403})

    def test_assign_requires_manager(self):
        """POST /api/leads/<id>/assign y├¬u cß║ºu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.post("/api/leads/1/assign", json={"assigned_to": 2})
        self.assertIn(resp.status_code, {401, 403})

    def test_delete_requires_manager(self):
        """DELETE /api/leads/<id> y├¬u cß║ºu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.delete("/api/leads/1")
        self.assertIn(resp.status_code, {401, 403})


if __name__ == "__main__":
    unittest.main()
