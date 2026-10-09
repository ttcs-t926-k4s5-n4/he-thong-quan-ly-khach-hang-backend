"""Kiểm thử tiêu chí chấp nhận SCRUM-79 — Nhập tay & nhập Excel hàng loạt."""
import io
import unittest

from openpyxl import load_workbook

from tests.base import ApiTestCase

HEADERS = ["Họ tên*", "Email", "Số điện thoại", "Công ty", "Nhu cầu quan tâm", "Nguồn", "Chi tiết nguồn"]


class Scrum79LeadImportTest(ApiTestCase):
    def upload(self, rows, filename="hoi-thao.xlsx", **form):
        data = {"file": (self.make_xlsx(rows), filename)}
        data.update(form)
        return self.client.post("/api/leads/import/preview", data=data, content_type="multipart/form-data")

    # ---------------- Nhập tay ----------------
    def test_ac79_01_nhap_tay_lead_tu_su_kien(self):
        res = self.client.post("/api/leads", json={
            "full_name": "Trần Thị Bình", "phone": "+84 912 000 111", "company": "XYZ",
            "source": "Danh thiếp", "source_detail": "Expo 2026"}, headers={"X-User-Id": "mkt01"})
        self.assertEqual(res.status_code, 201, res.get_json())
        lead = res.get_json()
        self.assertEqual(lead["status"], "Mới")
        self.assertEqual(lead["source"], "danh_thiep")
        self.assertEqual(lead["phone"], "0912000111")
        self.assertEqual(lead["created_by"], "mkt01")

    def test_ac79_02_nhap_tay_bat_buoc_co_nguon(self):
        res = self.client.post("/api/leads", json={"full_name": "A", "email": "a@x.vn"})
        self.assertEqual(res.status_code, 422)
        self.assertIn("source", res.get_json()["error"]["details"])
        res = self.client.post("/api/leads", json={"full_name": "A", "email": "a@x.vn", "source": "web_form"})
        self.assertEqual(res.status_code, 422)

    def test_ac79_03_can_it_nhat_email_hoac_sdt(self):
        res = self.client.post("/api/leads", json={"full_name": "A", "source": "su_kien"})
        self.assertEqual(res.status_code, 422)
        self.assertIn("contact", res.get_json()["error"]["details"])

    def test_ac79_04_canh_bao_trung_lead(self):
        self.client.post("/api/leads", json={"full_name": "A", "email": "a@x.vn", "source": "su_kien"})
        dup = self.client.post("/api/leads", json={"full_name": "B", "email": "A@X.VN", "source": "su_kien"})
        self.assertEqual(dup.status_code, 409)
        ok = self.client.post("/api/leads", json={"full_name": "B", "email": "a@x.vn", "source": "su_kien",
                                                  "allow_duplicate": True})
        self.assertEqual(ok.status_code, 201)

    # ---------------- Tệp mẫu ----------------
    def test_ac79_05_tai_tep_mau(self):
        res = self.client.get("/api/leads/import/template")
        self.assertEqual(res.status_code, 200)
        wb = load_workbook(io.BytesIO(res.data))
        headers = [c.value for c in wb.worksheets[0][1]]
        self.assertEqual(headers[0], "Họ tên*")
        self.assertIn("Nguồn", headers)
        self.assertEqual(len(wb.worksheets), 2)

    # ---------------- Nhập hàng loạt ----------------
    def test_ac79_06_xem_truoc_bao_loi_theo_tung_dong_khong_ghi_db(self):
        self.seed_lead(full_name="Cũ", email="cu@x.vn")
        res = self.upload([
            HEADERS,
            ["Lê Văn C", "c@x.vn", 912345678, "C Corp", "", "Hội thảo", "HT Chuyển đổi số"],  # hợp lệ (mất số 0)
            ["", "d@x.vn", "", "", "", "Hội thảo", ""],                                       # dòng 3: thiếu tên
            ["Phạm E", "sai-email", "", "", "", "Hội thảo", ""],                               # dòng 4: email sai
            ["Võ F", "c@x.vn", "", "", "", "Hội thảo", ""],                                    # dòng 5: trùng dòng 2
            ["Đỗ G", "cu@x.vn", "", "", "", "Hội thảo", ""],                                   # dòng 6: trùng hệ thống
            ["Hồ H", "h@x.vn", "", "", "", "Bay từ trên trời", ""],                            # dòng 7: nguồn sai
        ])
        self.assertEqual(res.status_code, 201, res.get_json())
        body = res.get_json()
        self.assertEqual((body["total_rows"], body["valid_rows"], body["error_rows"]), (6, 1, 5))
        error_rows = sorted({e["row_number"] for e in body["errors"]})
        self.assertEqual(error_rows, [3, 4, 5, 6, 7])
        self.assertEqual(body["rows"][0]["data"]["phone"], "0912345678")
        self.assertEqual(self.count_leads(), 1)   # xem trước không ghi DB

    def test_ac79_07_xac_nhan_chi_nhap_dong_hop_le_va_moi_lead_co_nguon(self):
        campaign_id = self.seed_campaign()
        res = self.upload([
            ["Họ tên", "Email", "SĐT", "Nguồn"],
            ["A1", "a1@x.vn", "", ""],
            ["A2", "a2@x.vn", "0988000111", "Sự kiện"],
            ["A3", "sai", "", ""],
        ], default_source="hoi_thao", source_detail="Hội thảo 10/10", campaign_id=str(campaign_id))
        preview = res.get_json()
        self.assertEqual(preview["valid_rows"], 2)
        commit = self.client.post(f"/api/leads/import/{preview['preview_id']}/commit", json={})
        self.assertEqual(commit.status_code, 201, commit.get_json())
        self.assertEqual(commit.get_json()["imported_count"], 2)
        self.assertEqual(commit.get_json()["skipped_count"], 1)
        leads = self.client.get(f"/api/leads?import_batch_id={preview['preview_id']}").get_json()["items"]
        self.assertEqual({l["source"] for l in leads}, {"hoi_thao", "su_kien"})
        self.assertTrue(all(l["source"] for l in leads))
        self.assertTrue(all(l["campaign_id"] == campaign_id for l in leads))
        self.assertTrue(all(l["status"] == "Mới" for l in leads))
        again = self.client.post(f"/api/leads/import/{preview['preview_id']}/commit", json={})
        self.assertEqual(again.status_code, 409)

    def test_ac79_08_khong_co_nguon_thi_dong_bi_loi(self):
        res = self.upload([["Họ tên", "Email"], ["A", "a@x.vn"]])
        body = res.get_json()
        self.assertEqual(body["error_rows"], 1)
        self.assertEqual(body["rows"][0]["errors"][0]["field"], "source")

    def test_ac79_09_all_or_nothing(self):
        res = self.upload([["Họ tên", "Email"], ["A", "a@x.vn"], ["B", "sai"]], default_source="su_kien")
        commit = self.client.post(f"/api/leads/import/{res.get_json()['id']}/commit", json={"mode": "all_or_nothing"})
        self.assertEqual(commit.status_code, 422)
        self.assertEqual(self.count_leads(), 0)

    def test_ac79_10_kiem_tra_tep_va_cot(self):
        bad_ext = self.client.post("/api/leads/import/preview",
                                   data={"file": (io.BytesIO(b"abc"), "a.pdf")}, content_type="multipart/form-data")
        self.assertEqual(bad_ext.status_code, 400)
        no_name = self.upload([["Email"], ["a@x.vn"]])
        self.assertEqual(no_name.status_code, 400)
        empty = self.upload([HEADERS])
        self.assertEqual(empty.status_code, 400)

    def test_ac79_11_ho_tro_csv(self):
        csv_bytes = "Họ tên;Email;Nguồn\nNguyễn A;a@x.vn;Giới thiệu\n".encode("utf-8-sig")
        res = self.client.post("/api/leads/import/preview", data={"file": (io.BytesIO(csv_bytes), "ds.csv")},
                               content_type="multipart/form-data")
        self.assertEqual(res.status_code, 201, res.get_json())
        self.assertEqual(res.get_json()["rows"][0]["data"]["source"], "gioi_thieu")


if __name__ == "__main__":
    unittest.main()
