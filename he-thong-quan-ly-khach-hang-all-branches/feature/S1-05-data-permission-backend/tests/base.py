"""Khung kiểm thử dùng chung: mỗi test có CSDL SQLite tạm, riêng biệt."""
import os
import tempfile
import unittest

from app import create_app
from app.db import init_db

# Id người dùng trong dữ liệu mẫu (xem app/db.py)
GIAM_DOC = 1
TRUONG_NHOM_BAC = 2   # nhóm 1
NHAN_VIEN_A = 3       # nhóm 1 — sở hữu khách hàng 1, 2
NHAN_VIEN_B = 4       # nhóm 1 — sở hữu khách hàng 3, 4
TRUONG_NHOM_NAM = 5   # nhóm 2
NHAN_VIEN_C = 6       # nhóm 2 — sở hữu khách hàng 5

KH_CUA_A = {1, 2}
KH_CUA_B = {3, 4}
KH_NHOM_BAC = {1, 2, 3, 4, 6}
KH_NHOM_NAM = {5, 7}
TAT_CA_KH = {1, 2, 3, 4, 5, 6, 7, 8}

RESOURCE_NAMES = ["customers", "opportunities", "activities", "quotes"]


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path})
        with self.app.app_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def get(self, url, user_id=None):
        headers = {"X-User-Id": str(user_id)} if user_id is not None else {}
        return self.client.get(url, headers=headers)

    def ids(self, url, user_id):
        res = self.get(url, user_id)
        self.assertEqual(res.status_code, 200, res.get_json())
        return {item["id"] for item in res.get_json()["items"]}
