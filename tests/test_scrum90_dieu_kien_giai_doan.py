"""SCRUM-90 – Điều kiện bắt buộc khi cơ hội rời một giai đoạn."""
from tests.base import CRMTestCase


class TestScrum90DieuKienGiaiDoan(CRMTestCase):
    def setUp(self):
        super().setUp()
        self.meeting_rule = self.add_rule(stage_id=self.stage("qualification"), rule_type="min_activities",
                                          activity_type="meeting", min_count=1)
        self.opp = self.make_opp()
        self.assertEqual(self.move(self.opp["id"], "qualification")[0], 200)

    def test_chi_giam_doc_duoc_cau_hinh(self):
        status, body = self.post("/api/stage-rules", "nhanvien1", {"stage_id": self.stage("proposal"),
                                                                    "rule_type": "min_product_lines"})
        self.assertEqual(status, 403)
        self.assertIn("Giám đốc kinh doanh", body["detail"])
        self.assertEqual(self.post("/api/stage-rules", "truongnhom1", {"stage_id": self.stage("proposal"),
                                                                        "rule_type": "min_product_lines"})[0], 403)
        self.assertEqual(self.meeting_rule["summary"],
                         "Khi rời giai đoạn \"Xác định nhu cầu\" (khi chuyển tiến): cần ít nhất 1 cuộc gặp đã diễn ra.")
        status, body = self.get("/api/stage-rules", "nhanvien1")
        self.assertEqual(len(body["items"]), 1)

    def test_chan_chuyen_khi_chua_co_cuoc_gap_va_neu_ro_dieu_kien_thieu(self):
        """Tiêu chí 1 + 2: không cho chuyển nếu chưa thoả; thông báo nêu rõ còn thiếu gì."""
        status, body = self.move(self.opp["id"], "proposal")
        self.assertEqual(status, 409)
        self.assertEqual(body["error_code"], "STAGE_CONDITIONS_UNMET")
        self.assertIn("còn thiếu 1 điều kiện", body["detail"])
        self.assertEqual(body["missing_conditions"][0]["message"],
                         "Cần ít nhất 1 cuộc gặp đã diễn ra được ghi nhận cho cơ hội (hiện có 0).")
        self.assertEqual(body["missing_conditions"][0]["stage_name"], "Xác định nhu cầu")
        self.assertFalse(body["can_override"])
        opp = self.get(f"/api/opportunities/{self.opp['id']}", "nhanvien1")[1]
        self.assertEqual(opp["stage"]["code"], "qualification")

    def test_cuoc_gap_sap_dien_ra_va_cuoc_goi_khong_duoc_tinh(self):
        self.log_meeting(self.opp["id"], occurred_at="2026-10-21T09:00:00")
        self.post("/api/activities", "nhanvien1", {"activity_type": "call", "opportunity_id": self.opp["id"],
                                                   "content": "Gọi chào hỏi."})
        self.assertEqual(self.move(self.opp["id"], "proposal")[0], 409)

    def test_thoa_dieu_kien_thi_chuyen_duoc(self):
        self.log_meeting(self.opp["id"])
        status, body = self.move(self.opp["id"], "proposal")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["opportunity"]["stage"]["code"], "proposal")
        self.assertEqual(body["opportunity"]["probability"], 40)

    def test_nhay_coc_phai_thoa_dieu_kien_cua_moi_giai_doan_bi_bo_qua(self):
        self.add_rule(stage_id=self.stage("proposal"), rule_type="min_product_lines", min_count=1)
        self.add_rule(stage_id=self.stage("quotation"), rule_type="min_amount", min_amount=200_000_000,
                      custom_message="Thương vụ dưới 200 triệu không cần qua đàm phán")
        status, body = self.move(self.opp["id"], "negotiation")
        self.assertEqual(status, 409)
        self.assertEqual([m["stage_name"] for m in body["missing_conditions"]],
                         ["Xác định nhu cầu", "Đề xuất giải pháp", "Báo giá"])
        self.assertEqual(body["missing_conditions"][2]["message"],
                         "Thương vụ dưới 200 triệu không cần qua đàm phán (hiện tại 100.000.000 đ).")
        self.assertEqual(self.move(self.opp["id"], "won")[0], 409)

    def test_chuyen_lui_hoac_sang_thua_khong_bi_chan(self):
        self.assertEqual(self.move(self.opp["id"], "prospecting")[0], 200)
        self.assertEqual(self.move(self.opp["id"], "qualification")[0], 200)
        self.assertEqual(self.move(self.opp["id"], "lost")[0], 200)

    def test_truong_nhom_tro_len_ghi_de_kem_ly_do(self):
        """Tiêu chí 3: trưởng nhóm trở lên có thể ghi đè kèm lý do."""
        status, body = self.move(self.opp["id"], "proposal", user="nhanvien1", override=True,
                                 override_reason="Khách gấp, đã gặp ngoài hệ thống.")
        self.assertEqual(status, 403)
        self.assertIn("Chỉ Trưởng nhóm trở lên", body["detail"])
        status, body = self.move(self.opp["id"], "proposal", user="truongnhom1")
        self.assertEqual(status, 409)
        self.assertTrue(body["can_override"])
        status, body = self.move(self.opp["id"], "proposal", user="truongnhom1", override=True)
        self.assertEqual(status, 422)
        self.assertFieldError(body, "override_reason", "lý do ghi đè")
        status, body = self.move(self.opp["id"], "proposal", user="truongnhom1", override=True,
                                 override_reason="Đã gặp khách tại hội chợ, biên bản gửi qua email.")
        self.assertEqual(status, 200, body)
        self.assertTrue(body["override_applied"])
        self.assertIn("Đã ghi đè 1 điều kiện", body["message"])

        history = self.get(f"/api/opportunities/{self.opp['id']}/stage-history", "nhanvien1")[1]["items"]
        last = history[-1]
        self.assertTrue(last["is_override"])
        self.assertEqual(last["override_reason"], "Đã gặp khách tại hội chợ, biên bản gửi qua email.")
        self.assertEqual(last["changed_by"]["full_name"], "Trần Thị Bình")
        self.assertEqual(len(last["unmet_conditions"]), 1)

        log = self.get("/api/stage-rules/overrides", "giamdoc")[1]
        self.assertEqual(log["total"], 1)
        self.assertEqual(self.get("/api/stage-rules/overrides", "truongnhom2")[1]["total"], 0)
        self.assertEqual(self.get("/api/stage-rules/overrides", "nhanvien1")[0], 403)

    def test_truong_nhom_khac_khong_ghi_de_duoc(self):
        status, _ = self.move(self.opp["id"], "proposal", user="truongnhom2", override=True,
                              override_reason="Thử ghi đè cơ hội của nhóm khác.")
        self.assertEqual(status, 404)

    def test_kiem_tra_truoc_khi_chuyen(self):
        url = f"/api/opportunities/{self.opp['id']}/stage-check"
        body = self.get(url, "nhanvien1")[1]
        self.assertEqual(body["to_stage"]["code"], "proposal")
        self.assertFalse(body["can_move"])
        self.assertEqual(len(body["missing_conditions"]), 1)
        self.log_meeting(self.opp["id"])
        body = self.get(url, "nhanvien1", {"to_stage_id": self.stage("proposal")})[1]
        self.assertTrue(body["can_move"])
        self.assertIn("đã đủ điều kiện", body["message"])

    def test_tao_moi_o_giai_doan_sau_cung_phai_thoa_dieu_kien(self):
        body = self.make_opp(expect=409, stage_id=self.stage("proposal"))
        self.assertEqual(body["error_code"], "STAGE_CONDITIONS_UNMET")
        opp = self.make_opp(user="truongnhom1", stage_id=self.stage("proposal"), override=True,
                            override_reason="Khách cũ tái ký, đã thống nhất phạm vi từ trước.")
        self.assertEqual(opp["stage"]["code"], "proposal")
        history = self.get(f"/api/opportunities/{opp['id']}/stage-history", "truongnhom1")[1]["items"]
        self.assertTrue(history[0]["is_override"])
        self.assertIsNone(history[0]["from_stage"])

    def test_bat_buoc_thong_tin_va_tat_dieu_kien(self):
        rule = self.add_rule(stage_id=self.stage("prospecting"), rule_type="required_field",
                             field_name="primary_contact_id")
        opp = self.make_opp(primary_contact_id=None)
        status, body = self.move(opp["id"], "qualification")
        self.assertEqual(status, 409)
        self.assertEqual(body["missing_conditions"][0]["message"], "Chưa có người liên hệ chính cho cơ hội.")
        status, body = self.patch(f"/api/stage-rules/{rule['id']}", "giamdoc", {"is_active": False})
        self.assertEqual(status, 200)
        self.assertEqual(self.move(opp["id"], "qualification")[0], 200)

    def test_kiem_tra_cau_hinh_khong_hop_le(self):
        status, body = self.post("/api/stage-rules", "giamdoc", {"stage_id": self.stage("won"),
                                                                  "rule_type": "min_product_lines"})
        self.assertEqual(status, 422)
        self.assertIn("đã đóng", body["detail"])
        status, body = self.post("/api/stage-rules", "giamdoc", {"stage_id": self.stage("proposal"),
                                                                  "rule_type": "required_field"})
        self.assertEqual(status, 422)
        self.assertFieldError(body, "field_name")
        status, body = self.post("/api/stage-rules", "giamdoc", {"stage_id": self.stage("qualification"),
                                                                  "rule_type": "min_activities",
                                                                  "activity_type": "meeting", "min_count": 1})
        self.assertEqual(status, 409)
        self.assertIn("đã tồn tại", body["detail"])
        status, body = self.delete(f"/api/stage-rules/{self.meeting_rule['id']}", "giamdoc")
        self.assertEqual(status, 200)
        self.assertEqual(self.move(self.opp["id"], "proposal")[0], 200)
