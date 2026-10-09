"""Kiểm thử tiêu chí chấp nhận SCRUM-78 — Biểu mẫu nhúng thu thập lead."""
import time
import unittest

from tests.base import ApiTestCase

VALID = {"full_name": "Nguyễn Văn An", "email": "an@abc.vn", "phone": "0912 345 678",
         "company": "ABC", "interest": "Phần mềm CRM"}


class Scrum78WebFormTest(ApiTestCase):
    def create_form(self, **kw):
        body = {"name": "Form trang chủ"}
        body.update(kw)
        res = self.client.post("/api/forms", json=body)
        self.assertEqual(res.status_code, 201, res.get_json())
        return res.get_json()

    def submit(self, key, data=None, ip="1.1.1.1", headers=None):
        h = {"X-Forwarded-For": ip}
        h.update(headers or {})
        return self.client.post(f"/public/forms/{key}/submit", json=data or VALID, headers=h)

    def test_ac78_01_tao_bieu_mau_sinh_ma_nhung(self):
        form = self.create_form()
        self.assertIn("<script", form["embed"]["script"])
        self.assertIn(f"/embed/{form['public_key']}.js", form["embed"]["script"])
        self.assertIn("<iframe", form["embed"]["iframe"])
        res = self.client.get(f"/api/forms/{form['id']}/embed-code")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["public_key"], form["public_key"])

    def test_ac78_02_script_nhung_render_du_5_truong(self):
        form = self.create_form()
        res = self.client.get(f"/embed/{form['public_key']}.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn("javascript", res.content_type)
        js = res.get_data(as_text=True)
        for field in ("full_name", "email", "phone", "company", "interest", "website_url"):
            self.assertIn(field, js)
        self.assertEqual(self.client.get(f"/embed/{form['public_key']}/page").status_code, 200)

    def test_ac78_03_gui_thanh_cong_tao_lead_moi_dung_nguon(self):
        campaign_id = self.seed_campaign()
        form = self.create_form(campaign_id=campaign_id)
        res = self.submit(form["public_key"])
        self.assertEqual(res.status_code, 201, res.get_json())
        lead = self.client.get("/api/leads").get_json()["items"][0]
        self.assertEqual(lead["status"], "Mới")
        self.assertEqual(lead["source"], "web_form")
        self.assertEqual(lead["form_id"], form["id"])
        self.assertEqual(lead["campaign_id"], campaign_id)
        self.assertEqual(lead["source_detail"], "Form trang chủ")
        self.assertEqual(lead["phone"], "0912345678")

    def test_ac78_04_du_lieu_sai_bao_loi_tung_truong(self):
        form = self.create_form()
        res = self.submit(form["public_key"], {"full_name": "", "email": "sai-email", "phone": "123"})
        self.assertEqual(res.status_code, 422)
        details = res.get_json()["error"]["details"]
        self.assertEqual(set(details), {"full_name", "email", "phone"})
        self.assertEqual(self.count_leads(), 0)

    def test_ac78_05_honeypot_chan_bot_ma_khong_bao_loi(self):
        form = self.create_form()
        res = self.submit(form["public_key"], {**VALID, "website_url": "http://spam.com"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self.count_leads(), 0)

    def test_ac78_06_gui_qua_nhanh_bi_xem_la_spam(self):
        form = self.create_form()
        self.submit(form["public_key"], {**VALID, "_ts": time.time() * 1000})
        self.assertEqual(self.count_leads(), 0)
        self.submit(form["public_key"], {**VALID, "_ts": time.time() * 1000 - 10_000}, ip="2.2.2.2")
        self.assertEqual(self.count_leads(), 1)

    def test_ac78_07_gioi_han_tan_suat_theo_ip(self):
        form = self.create_form()
        for i in range(5):
            data = {**VALID, "email": f"u{i}@abc.vn"}
            self.assertEqual(self.submit(form["public_key"], data).status_code, 201)
        res = self.submit(form["public_key"], {**VALID, "email": "u9@abc.vn"})
        self.assertEqual(res.status_code, 429)
        self.assertIn("Retry-After", res.headers)
        self.assertEqual(self.submit(form["public_key"], ip="9.9.9.9").status_code, 201)

    def test_ac78_08_chi_domain_duoc_phep_moi_gui_duoc(self):
        form = self.create_form(allowed_domains=["https://congty.vn"])
        self.assertEqual(form["allowed_domains"], ["congty.vn"])
        bad = self.submit(form["public_key"], headers={"Origin": "https://evil.com"})
        self.assertEqual(bad.status_code, 403)
        ok = self.submit(form["public_key"], headers={"Origin": "https://www.congty.vn"}, ip="3.3.3.3")
        self.assertEqual(ok.status_code, 201)

    def test_ac78_09_bieu_mau_tat_khong_nhan_du_lieu(self):
        form = self.create_form()
        res = self.client.patch(f"/api/forms/{form['id']}", json={"is_active": False})
        self.assertFalse(res.get_json()["is_active"])
        self.assertEqual(self.submit(form["public_key"]).status_code, 404)

    def test_ac78_10_validate_khi_tao_bieu_mau(self):
        res = self.client.post("/api/forms", json={"name": "", "allowed_domains": ["không hợp lệ"],
                                                   "campaign_id": 999})
        self.assertEqual(res.status_code, 422)
        self.assertEqual(set(res.get_json()["error"]["details"]), {"name", "allowed_domains", "campaign_id"})


if __name__ == "__main__":
    unittest.main()
