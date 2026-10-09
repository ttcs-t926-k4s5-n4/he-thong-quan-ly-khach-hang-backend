"""Lớp test dùng chung: mỗi test chạy trên một CSDL SQLite tạm, độc lập."""
import io
import os
import tempfile
import unittest

from openpyxl import Workbook

from app import create_app
from app.core import get_db, insert_lead, now_iso


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "DB_PATH": os.path.join(self._tmp.name, "test.db"),
            "TRUST_PROXY": True,
            "MIN_FILL_SECONDS": 3,
            "RATE_LIMIT_PER_FORM": "5/600",
            "RATE_LIMIT_PER_IP": "20/3600",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    # ---- seed trực tiếp vào DB để mỗi feature test độc lập với feature khác ----
    def seed_campaign(self, name="Hội thảo CĐS 2026", channel="hoi_thao", budget=10_000_000,
                      start="2026-01-01", end="2026-12-31"):
        with self.app.app_context():
            db = get_db()
            ts = now_iso()
            cur = db.execute(
                "INSERT INTO campaigns (name, channel, budget, start_date, end_date, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", (name, channel, budget, start, end, ts, ts))
            db.commit()
            return cur.lastrowid

    def seed_lead(self, **kw):
        data = {"full_name": "Khách Mẫu", "source": "hoi_thao", "email": None, "phone": None}
        data.update(kw)
        with self.app.app_context():
            return insert_lead(get_db(), data)

    def count_leads(self):
        with self.app.app_context():
            return get_db().execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    @staticmethod
    def make_xlsx(rows):
        wb = Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf
