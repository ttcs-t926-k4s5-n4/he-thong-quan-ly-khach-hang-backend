"""Kiểm thử tiêu chí chấp nhận SCRUM-80 — Theo dõi lead theo chiến dịch & doanh thu."""
import unittest

from tests.base import ApiTestCase

CAMPAIGN = {"name": "Facebook Ads Q4", "channel": "facebook", "budget": 20_000_000,
            "start_date": "2026-10-01", "end_date": "2026-12-31"}


class Scrum80CampaignTrackingTest(ApiTestCase):
    def create_campaign(self, **kw):
        res = self.client.post("/api/campaigns", json={**CAMPAIGN, **kw})
        self.assertEqual(res.status_code, 201, res.get_json())
        return res.get_json()

    def test_ac80_01_khai_bao_chien_dich_day_du(self):
        c = self.create_campaign()
        self.assertEqual(c["budget"], 20_000_000)
        self.assertEqual(c["channel_label"], "Facebook")
        self.assertIn(c["status"], ("Sắp chạy", "Đang chạy", "Đã kết thúc"))

    def test_ac80_02_validate_chien_dich(self):
        res = self.client.post("/api/campaigns", json={"name": "", "channel": "tivi", "budget": -5,
                                                       "start_date": "2026-12-01", "end_date": "2026-11-01"})
        self.assertEqual(res.status_code, 422)
        self.assertEqual(set(res.get_json()["error"]["details"]), {"name", "channel", "budget", "end_date"})
        self.create_campaign()
        self.assertEqual(self.client.post("/api/campaigns", json=CAMPAIGN).status_code, 409)

    def test_ac80_03_sua_chien_dich(self):
        c = self.create_campaign()
        res = self.client.patch(f"/api/campaigns/{c['id']}", json={"budget": 25_000_000})
        self.assertEqual(res.get_json()["budget"], 25_000_000)
        bad = self.client.patch(f"/api/campaigns/{c['id']}", json={"end_date": "2025-01-01"})
        self.assertEqual(bad.status_code, 422)

    def test_ac80_04_chuyen_doi_lead_co_hoi_ke_thua_chien_dich(self):
        c = self.create_campaign()
        lead_id = self.seed_lead(full_name="Khách A", campaign_id=c["id"], company="A Corp")
        res = self.client.post(f"/api/leads/{lead_id}/convert", json={"value": 50_000_000})
        self.assertEqual(res.status_code, 201, res.get_json())
        body = res.get_json()
        self.assertEqual(body["opportunity"]["campaign_id"], c["id"])
        self.assertEqual(body["opportunity"]["lead_id"], lead_id)
        self.assertEqual(body["lead"]["status"], "Đã chuyển đổi")
        self.assertEqual(self.client.post(f"/api/leads/{lead_id}/convert", json={}).status_code, 409)

    def test_ac80_05_khong_the_doi_chien_dich_goc(self):
        c1, c2 = self.create_campaign(), self.create_campaign(name="Google Q4", channel="google_ads")
        lead_id = self.seed_lead(campaign_id=c1["id"])
        self.assertEqual(self.client.patch(f"/api/leads/{lead_id}", json={"campaign_id": c2["id"]}).status_code, 422)
        self.assertEqual(self.client.post(f"/api/leads/{lead_id}/convert",
                                          json={"campaign_id": c2["id"]}).status_code, 422)
        opp = self.client.post(f"/api/leads/{lead_id}/convert", json={}).get_json()["opportunity"]
        self.assertEqual(self.client.patch(f"/api/opportunities/{opp['id']}",
                                           json={"campaign_id": c2["id"]}).status_code, 422)
        wrong = self.client.post("/api/opportunities", json={"name": "X", "lead_id": lead_id, "campaign_id": c2["id"]})
        self.assertEqual(wrong.status_code, 422)

    def test_ac80_06_co_hoi_thang_phai_co_gia_tri(self):
        c = self.create_campaign()
        opp = self.client.post("/api/opportunities", json={"name": "Deal", "campaign_id": c["id"]}).get_json()
        bad = self.client.patch(f"/api/opportunities/{opp['id']}", json={"stage": "Thắng"})
        self.assertEqual(bad.status_code, 422)
        ok = self.client.patch(f"/api/opportunities/{opp['id']}", json={"stage": "Thắng", "value": 1_000_000})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.get_json()["is_closed"])
        self.assertIsNotNone(ok.get_json()["closed_at"])

    def _seed_two_campaigns(self):
        many = self.create_campaign(name="Nhiều lead", budget=10_000_000)
        rich = self.create_campaign(name="Ra doanh thu", channel="hoi_thao", budget=20_000_000)
        many_leads = [self.seed_lead(full_name=f"M{i}", campaign_id=many["id"]) for i in range(10)]
        rich_leads = [self.seed_lead(full_name=f"R{i}", campaign_id=rich["id"]) for i in range(3)]
        o = self.client.post(f"/api/leads/{many_leads[0]}/convert", json={}).get_json()["opportunity"]
        self.client.patch(f"/api/opportunities/{o['id']}", json={"stage": "Thắng", "value": 5_000_000})
        o = self.client.post(f"/api/leads/{many_leads[1]}/convert", json={}).get_json()["opportunity"]
        self.client.patch(f"/api/opportunities/{o['id']}", json={"stage": "Thua"})
        for lead_id, value in zip(rich_leads[:2], (60_000_000, 40_000_000)):
            o = self.client.post(f"/api/leads/{lead_id}/convert", json={}).get_json()["opportunity"]
            self.client.patch(f"/api/opportunities/{o['id']}", json={"stage": "Thắng", "value": value})
        o = self.client.post(f"/api/leads/{rich_leads[2]}/convert", json={"value": 7_000_000}).get_json()
        return many, rich

    def test_ac80_07_bao_cao_tung_chien_dich(self):
        many, rich = self._seed_two_campaigns()
        r = self.client.get(f"/api/campaigns/{rich['id']}/report").get_json()
        self.assertEqual(r["lead_count"], 3)
        self.assertEqual(r["opportunity_count"], 3)
        self.assertEqual(r["won_count"], 2)
        self.assertEqual(r["won_value"], 100_000_000)
        self.assertEqual(r["pipeline_value"], 7_000_000)
        self.assertEqual(r["cost_per_lead"], round(20_000_000 / 3, 2))
        self.assertEqual(r["roi_percent"], 400.0)
        m = self.client.get(f"/api/campaigns/{many['id']}/report").get_json()
        self.assertEqual((m["lead_count"], m["opportunity_count"], m["won_value"], m["win_rate"]),
                         (10, 2, 5_000_000, 50.0))
        self.assertEqual(m["roi_percent"], -50.0)

    def test_ac80_08_xep_hang_theo_doanh_thu_khong_theo_so_lead(self):
        many, rich = self._seed_two_campaigns()
        self.seed_lead(full_name="Không chiến dịch")
        rep = self.client.get("/api/reports/campaigns").get_json()
        self.assertEqual([i["campaign_id"] for i in rep["items"]], [rich["id"], many["id"]])
        self.assertEqual(rep["top_by_revenue"], rich["id"])
        self.assertEqual(rep["top_by_leads"], many["id"])
        self.assertIsNotNone(rep["insight"])
        self.assertEqual(rep["totals"]["won_value"], 105_000_000)
        self.assertEqual(rep["unassigned"]["lead_count"], 1)
        by_leads = self.client.get("/api/reports/campaigns?sort=lead_count").get_json()
        self.assertEqual(by_leads["items"][0]["campaign_id"], many["id"])

    def test_ac80_09_danh_sach_lead_cua_chien_dich(self):
        c = self.create_campaign()
        self.seed_lead(campaign_id=c["id"])
        self.seed_lead()
        res = self.client.get(f"/api/campaigns/{c['id']}/leads").get_json()
        self.assertEqual(res["total"], 1)


if __name__ == "__main__":
    unittest.main()
