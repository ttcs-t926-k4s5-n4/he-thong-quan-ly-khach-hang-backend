"""SCRUM-88 – Điều hành cơ hội trên bảng pipeline dạng kanban."""
from datetime import datetime

from tests.base import CRMTestCase


class TestScrum88Pipeline(CRMTestCase):
    def column(self, board, code):
        return next(c for c in board["columns"] if c["stage"]["code"] == code)

    def test_moi_cot_la_mot_giai_doan_co_so_luong_va_tong_gia_tri(self):
        """Tiêu chí 1: mỗi cột là một giai đoạn, hiển thị số cơ hội và tổng giá trị của cột."""
        self.make_opp(estimated_value=100_000_000)
        self.make_opp(estimated_value=50_000_000)
        third = self.make_opp(estimated_value=30_000_000)
        self.assertEqual(self.move(third["id"], "qualification")[0], 200)
        status, board = self.get("/api/pipeline/board", "nhanvien1")
        self.assertEqual(status, 200)
        self.assertEqual([c["stage"]["name"] for c in board["columns"]],
                         ["Tiếp cận", "Xác định nhu cầu", "Đề xuất giải pháp", "Báo giá", "Đàm phán", "Thắng", "Thua"])
        prospecting = self.column(board, "prospecting")
        self.assertEqual((prospecting["count"], prospecting["total_amount"]), (2, 150_000_000))
        qualification = self.column(board, "qualification")
        self.assertEqual((qualification["count"], qualification["total_amount"]), (1, 30_000_000))
        self.assertEqual(qualification["weighted_amount"], 6_000_000)
        self.assertEqual(board["summary"]["count"], 3)

    def test_the_hien_thi_ten_khach_gia_tri_ngay_chot(self):
        """Tiêu chí 3: thẻ hiển thị tên khách, giá trị, ngày dự kiến chốt."""
        self.make_opp(estimated_value=75_000_000, expected_close_date="2026-12-20")
        card = self.column(self.get("/api/pipeline/board", "nhanvien1")[1], "prospecting")["cards"][0]
        self.assertEqual(card["customer_name"], "Công ty CP Công nghệ Ánh Dương")
        self.assertEqual(card["amount"], 75_000_000)
        self.assertEqual(card["expected_close_date"], "2026-12-20")
        self.assertFalse(card["is_stale"])
        self.assertEqual(card["warnings"], [])

    def test_canh_bao_dinh_tre(self):
        """Tiêu chí 3: cảnh báo khi cơ hội đình trệ ở một giai đoạn quá ngưỡng."""
        self.make_opp(expected_close_date="2027-01-31")
        self.at(datetime(2026, 11, 8, 9, 0))  # 20 ngày sau, ngưỡng giai đoạn Tiếp cận là 14 ngày
        card = self.column(self.get("/api/pipeline/board", "nhanvien1")[1], "prospecting")["cards"][0]
        self.assertTrue(card["is_stale"])
        self.assertEqual(card["days_in_stage"], 20)
        self.assertEqual(card["warning_level"], "warning")
        self.assertTrue(any("Đình trệ" in w and "20 ngày" in w for w in card["warnings"]))
        self.assertTrue(any("Chưa có hoạt động" in w for w in card["warnings"]))

    def test_hoat_dong_gan_day_lam_mat_canh_bao_khong_hoat_dong(self):
        opp = self.make_opp(expected_close_date="2027-01-31")
        self.at(datetime(2026, 10, 30, 9, 0))
        self.log_meeting(opp["id"], occurred_at="2026-10-29T10:00:00")
        self.at(datetime(2026, 11, 2, 9, 0))  # 14 ngày ở giai đoạn: chưa vượt ngưỡng
        card = self.column(self.get("/api/pipeline/board", "nhanvien1")[1], "prospecting")["cards"][0]
        self.assertFalse(card["is_stale"])
        self.assertEqual(card["last_activity_at"], "2026-10-29T10:00:00")

    def test_canh_bao_qua_ngay_du_kien_chot(self):
        self.make_opp(expected_close_date="2026-10-24")
        self.at(datetime(2026, 10, 27, 9, 0))
        card = self.column(self.get("/api/pipeline/board", "nhanvien1")[1], "prospecting")["cards"][0]
        self.assertTrue(card["is_overdue"])
        self.assertEqual(card["warning_level"], "danger")
        self.assertIn("Đã quá ngày dự kiến chốt 3 ngày (24/10/2026).", card["warnings"])

    def test_keo_tha_de_chuyen_giai_doan(self):
        """Tiêu chí 2: kéo thả để chuyển giai đoạn, trả về số liệu mới của các cột."""
        opp = self.make_opp(estimated_value=40_000_000)
        status, body = self.post(f"/api/pipeline/cards/{opp['id']}/move", "nhanvien1",
                                 {"to_stage_id": self.stage("qualification")})
        self.assertEqual(status, 200, body)
        self.assertTrue(body["changed"])
        self.assertEqual(body["card"]["stage_id"], self.stage("qualification"))
        self.assertIn("sang \"Xác định nhu cầu\"", body["message"])
        columns = {c["stage_name"]: c for c in body["columns"]}
        self.assertEqual(columns["Tiếp cận"]["count"], 0)
        self.assertEqual((columns["Xác định nhu cầu"]["count"], columns["Xác định nhu cầu"]["total_amount"]),
                         (1, 40_000_000))
        status, body = self.post(f"/api/pipeline/cards/{opp['id']}/move", "nhanvien1",
                                 {"to_stage_id": self.stage("qualification")})
        self.assertEqual(status, 200)
        self.assertFalse(body["changed"])

    def test_keo_tha_bi_chan_khi_thieu_dieu_kien(self):
        self.add_rule(stage_id=self.stage("prospecting"), rule_type="required_field", field_name="description")
        opp = self.make_opp()
        status, body = self.post(f"/api/pipeline/cards/{opp['id']}/move", "nhanvien1",
                                 {"to_stage_id": self.stage("qualification")})
        self.assertEqual(status, 409)
        self.assertEqual(body["error_code"], "STAGE_CONDITIONS_UNMET")
        self.assertIn("Chưa có mô tả nhu cầu cho cơ hội.", body["missing_conditions"][0]["message"])

    def test_nhan_vien_mac_dinh_chi_thay_co_hoi_cua_minh(self):
        """Tiêu chí 4: nhân viên mặc định chỉ thấy cơ hội của mình."""
        self.make_opp(user="nhanvien1")
        self.make_opp(user="nhanvien2", customer_id=self.customer("an_khang"),
                      primary_contact_id=self.contact("Trịnh Thu Hà"))
        self.make_opp(user="nhanvien3", customer_id=self.customer("sao_viet"),
                      primary_contact_id=self.contact("Đặng Hoài Nam"))
        board = self.get("/api/pipeline/board", "nhanvien1")[1]
        self.assertEqual(board["scope_label"], "Cơ hội của tôi")
        self.assertEqual(board["summary"]["count"], 1)
        self.assertEqual(self.get("/api/pipeline/board", "truongnhom1")[1]["summary"]["count"], 2)
        self.assertEqual(self.get("/api/pipeline/board", "giamdoc")[1]["summary"]["count"], 3)
        status, body = self.get("/api/pipeline/board", "nhanvien1", {"owner_id": self.uid("nhanvien2")})
        self.assertEqual(status, 403)
        self.assertEqual(body["detail"], "Nhân viên chỉ được xem cơ hội của chính mình.")

    def test_loc_theo_nguoi_so_huu_nhom_khoang_ngay_chot(self):
        """Tiêu chí 4: lọc theo người sở hữu, nhóm, khoảng ngày chốt."""
        self.make_opp(user="nhanvien1", expected_close_date="2026-11-10")
        self.make_opp(user="nhanvien1", expected_close_date="2026-12-20")
        self.make_opp(user="nhanvien2", customer_id=self.customer("an_khang"),
                      primary_contact_id=self.contact("Trịnh Thu Hà"), expected_close_date="2026-11-15")
        self.make_opp(user="nhanvien3", customer_id=self.customer("sao_viet"),
                      primary_contact_id=self.contact("Đặng Hoài Nam"), expected_close_date="2026-11-20")
        board = self.get("/api/pipeline/board", "truongnhom1", {"owner_id": self.uid("nhanvien2")})[1]
        self.assertEqual((board["summary"]["count"], board["scope_label"]), (1, "Cơ hội của Phạm Thị Dung"))
        board = self.get("/api/pipeline/board", "giamdoc", {"team_id": self.ids["teams"][1]})[1]
        self.assertEqual(board["summary"]["count"], 1)
        board = self.get("/api/pipeline/board", "giamdoc", {"close_from": "2026-11-01", "close_to": "2026-11-30"})[1]
        self.assertEqual(board["summary"]["count"], 3)
        self.assertEqual(self.get("/api/pipeline/board", "truongnhom1",
                                  {"team_id": self.ids["teams"][1]})[0], 403)
        self.assertEqual(self.get("/api/pipeline/board", "truongnhom1",
                                  {"owner_id": self.uid("nhanvien3")})[0], 403)
        status, body = self.get("/api/pipeline/board", "giamdoc", {"close_from": "2026-12-01",
                                                                   "close_to": "2026-11-01"})
        self.assertEqual(status, 422)
        self.assertFieldError(body, "close_to", "Ngày chốt đến")

    def test_an_cot_da_dong(self):
        board = self.get("/api/pipeline/board", "nhanvien1", {"include_closed": "false"})[1]
        self.assertEqual(len(board["columns"]), 5)
