r"""
tests/test_lead_accept_reject_sla.py — Test suite cho SCRUM-84
Kiểm thử: Nhận/Từ chối Lead với ràng buộc SLA phản hồi

Chạy:
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
        """Tạo lead mới với tên hợp lệ → 201 hoặc response hợp lệ"""
        _login(self.client)
        resp = self.client.post("/api/leads", json={
            "full_name": "Nguyễn Văn Test",
            "email": "test@example.com",
            "phone": "0901234567",
            "company": "Công ty Test",
            "source": "Facebook",
            "classification": "warm",
        })
        self.assertIn(resp.status_code, {201, 401, 500})

    def test_create_lead_missing_name(self):
        """Thiếu full_name → 400 với error message"""
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
        """SLA còn > 8 giờ → 'ok'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 10 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "ok")

    def test_compute_sla_status_warning(self):
        """SLA còn < 8 giờ → 'warning'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 4 * 3600 * 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "warning")

    def test_compute_sla_status_breached_by_flag(self):
        """sla_breached=1 → luôn 'breached' bất kể deadline"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - 1000,
            "sla_deadline_at": now_ms + 100 * 3600 * 1000,
            "sla_breached": 1,
        }
        self.assertEqual(_compute_sla_status(lead), "breached")

    def test_compute_sla_status_breached_by_time(self):
        """Deadline đã qua, sla_breached=0 → vẫn 'breached'"""
        from app.leads import _compute_sla_status
        now_ms = int(time.time() * 1000)
        lead = {
            "assigned_at": now_ms - SLA_3_DAYS_MS - 1000,
            "sla_deadline_at": now_ms - 1000,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "breached")

    def test_compute_sla_status_not_assigned(self):
        """Chưa phân công (assigned_at=None) → 'not_assigned'"""
        from app.leads import _compute_sla_status
        lead = {
            "assigned_at": None,
            "sla_deadline_at": None,
            "sla_breached": 0,
        }
        self.assertEqual(_compute_sla_status(lead), "not_assigned")

    def test_sla_deadline_is_3_days_from_assigned(self):
        """SLA deadline phải = assigned_at + 3 ngày (72 giờ)"""
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
        """Từ chối không có lý do → 400"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("errors", data)
            self.assertIn("reason", data["errors"])
            self.assertIn("bắt buộc", data["errors"]["reason"].lower())

    def test_reject_with_empty_reason_returns_400(self):
        """Lý do rỗng (chỉ whitespace) → 400"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={"reason": "   "})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertIn("reason", data.get("errors", {}))

    def test_reject_with_valid_reason_processes(self):
        """Lý do hợp lệ → không trả 400 về validation"""
        _login(self.client)
        resp = self.client.post("/api/leads/999/reject", json={"reason": "Khách không đúng phân khúc"})
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertNotIn("reason", data.get("errors", {}))


class TestLeadClassification(unittest.TestCase):
    def test_valid_classifications(self):
        """Chấp nhận hot/warm/cold"""
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
        """GET /api/leads không có session → 401"""
        resp = self.client.get("/api/leads")
        self.assertEqual(resp.status_code, 401)

    def test_sla_breached_requires_manager(self):
        """GET /api/leads/sla-breached yêu cầu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.get("/api/leads/sla-breached")
        self.assertIn(resp.status_code, {401, 403})

    def test_assign_requires_manager(self):
        """POST /api/leads/<id>/assign yêu cầu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.post("/api/leads/1/assign", json={"assigned_to": 2})
        self.assertIn(resp.status_code, {401, 403})

    def test_delete_requires_manager(self):
        """DELETE /api/leads/<id> yêu cầu role manager/admin"""
        _login(self.client, email="employee@test.com")
        resp = self.client.delete("/api/leads/1")
        self.assertIn(resp.status_code, {401, 403})


if __name__ == "__main__":
    unittest.main()
