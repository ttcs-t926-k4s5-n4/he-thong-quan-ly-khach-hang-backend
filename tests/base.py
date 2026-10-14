"""Lớp kiểm thử cơ sở: CSDL tạm, dữ liệu nền, đồng hồ đóng băng, gọi API với token."""
import os
import tempfile
import unittest
from datetime import datetime

from app import clock, create_app, seed
from app.auth import create_token
from app.db import commit, init_db

# Thứ Hai 19/10/2026, 9 giờ sáng (giờ Việt Nam)
NOW = datetime(2026, 10, 19, 9, 0, 0)


class CRMTestCase(unittest.TestCase):
    def setUp(self):
        clock.freeze(NOW)
        handle, self.db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(handle)
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path, "SECRET_KEY": "khoa-kiem-thu",
                               "AUTO_INIT_DB": False})
        with self.app.app_context():
            init_db()
            self.ids = seed.seed_base()
            commit()
            self.tokens = {name: create_token(uid) for name, uid in self.ids["users"].items()}
        self.client = self.app.test_client()

    def tearDown(self):
        clock.unfreeze()
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    # ------------------------------------------------------------ gọi API
    def call(self, method, url, user=None, json=None, query=None):
        headers = {"Authorization": f"Bearer {self.tokens[user]}"} if user else {}
        response = self.client.open(url, method=method, json=json, query_string=query, headers=headers)
        return response.status_code, response.get_json()

    def get(self, url, user, query=None):
        return self.call("GET", url, user, query=query)

    def post(self, url, user, json=None, query=None):
        return self.call("POST", url, user, json=json if json is not None else {}, query=query)

    def patch(self, url, user, json):
        return self.call("PATCH", url, user, json=json)

    def delete(self, url, user):
        return self.call("DELETE", url, user)

    # ------------------------------------------------------------ tiện ích dữ liệu
    def uid(self, username):
        return self.ids["users"][username]

    def stage(self, code):
        return self.ids["stages"][code]

    def customer(self, key):
        return self.ids["customers"][key]

    def contact(self, name):
        return self.ids["contacts"][name]

    def product(self, code):
        return self.ids["products"][code]

    def at(self, moment):
        clock.freeze(moment)

    def make_opp(self, user="nhanvien1", expect=201, **overrides):
        payload = {
            "name": "Cơ hội thử nghiệm",
            "customer_id": self.customer("anh_duong"),
            "primary_contact_id": self.contact("Đỗ Minh Hải"),
            "estimated_value": 100_000_000,
            "expected_close_date": "2026-11-30",
            "source": "referral",
        }
        payload.update(overrides)
        status, body = self.post("/api/opportunities", user, payload)
        self.assertEqual(status, expect, body)
        return body["opportunity"] if status == 201 else body

    def move(self, opp_id, code, user="nhanvien1", **extra):
        return self.post(f"/api/opportunities/{opp_id}/change-stage", user,
                         {"to_stage_id": self.stage(code), **extra})

    def add_rule(self, **payload):
        status, body = self.post("/api/stage-rules", "giamdoc", payload)
        self.assertEqual(status, 201, body)
        return body["rule"]

    def log_meeting(self, opp_id, user="nhanvien1", **extra):
        payload = {"activity_type": "meeting", "opportunity_id": opp_id, "content": "Gặp khách trao đổi nhu cầu.",
                   "occurred_at": "2026-10-18T14:00:00", "duration_minutes": 60}
        payload.update(extra)
        status, body = self.post("/api/activities", user, payload)
        self.assertEqual(status, 201, body)
        return body["activity"]

    def assertFieldError(self, body, field, contains=None):
        fields = {e["field"]: e["message"] for e in body.get("errors", [])}
        self.assertIn(field, fields, body)
        if contains:
            self.assertIn(contains, fields[field])
