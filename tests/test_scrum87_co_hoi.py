"""SCRUM-87 – Tạo và quản lý cơ hội bán hàng."""
from tests.base import CRMTestCase


class TestScrum87CoHoi(CRMTestCase):
    def test_khai_bao_day_du_thong_tin(self):
        """Tiêu chí 1: tên, khách hàng, người liên hệ chính, giai đoạn, giá trị dự kiến, ngày dự kiến chốt, nguồn."""
        opp = self.make_opp(name="Triển khai CRM", stage_id=self.stage("prospecting"), estimated_value=250_000_000,
                            expected_close_date="2026-12-15", source="website")
        self.assertEqual(opp["name"], "Triển khai CRM")
        self.assertEqual(opp["customer"]["name"], "Công ty CP Công nghệ Ánh Dương")
        self.assertEqual(opp["primary_contact"]["full_name"], "Đỗ Minh Hải")
        self.assertEqual(opp["stage"]["name"], "Tiếp cận")
        self.assertEqual(opp["estimated_value"], 250_000_000)
        self.assertEqual(opp["amount"], 250_000_000)
        self.assertEqual(opp["expected_close_date"], "2026-12-15")
        self.assertEqual(opp["source_label"], "Website")
        self.assertEqual(opp["owner"]["id"], self.uid("nhanvien1"))
        self.assertEqual(opp["status_label"], "Đang mở")

    def test_mac_dinh_giai_doan_dau_tien(self):
        opp = self.make_opp()
        self.assertEqual(opp["stage"]["code"], "prospecting")

    def test_xac_suat_mac_dinh_theo_giai_doan(self):
        """Tiêu chí 2: xác suất thắng lấy mặc định theo giai đoạn."""
        opp = self.make_opp(stage_id=self.stage("qualification"))
        self.assertEqual(opp["probability"], 20)
        self.assertFalse(opp["probability_is_manual"])

    def test_sua_tay_xac_suat_bat_buoc_ghi_chu(self):
        """Tiêu chí 2: sửa tay được nhưng phải kèm ghi chú."""
        body = self.make_opp(expect=422, probability=35)
        self.assertFieldError(body, "probability_note", "Vui lòng nhập ghi chú")
        opp = self.make_opp(probability=35, probability_note="Khách đã có ngân sách được duyệt.")
        self.assertEqual(opp["probability"], 35)
        self.assertTrue(opp["probability_is_manual"])
        self.assertEqual(opp["probability_note"], "Khách đã có ngân sách được duyệt.")

        status, body = self.patch(f"/api/opportunities/{opp['id']}", "nhanvien1", {"probability": 50})
        self.assertEqual(status, 422)
        self.assertFieldError(body, "probability_note")
        status, body = self.patch(f"/api/opportunities/{opp['id']}", "nhanvien1",
                                  {"probability": 50, "probability_note": "Khách xác nhận lịch ký hợp đồng."})
        self.assertEqual(status, 200, body)
        self.assertEqual(body["opportunity"]["probability"], 50)
        status, body = self.patch(f"/api/opportunities/{opp['id']}", "nhanvien1", {"probability": 10})
        self.assertEqual(status, 200)
        self.assertFalse(body["opportunity"]["probability_is_manual"])
        self.assertIsNone(body["opportunity"]["probability_note"])

    def test_mot_khach_hang_nhieu_co_hoi_song_song(self):
        """Tiêu chí 3: một khách hàng có thể có nhiều cơ hội song song."""
        self.make_opp(name="Cơ hội phần mềm")
        status, body = self.post("/api/opportunities", "nhanvien1", {
            "name": "Cơ hội thiết bị", "customer_id": self.customer("anh_duong"),
            "expected_close_date": "2026-12-01"})
        self.assertEqual(status, 201)
        self.assertIn("2 cơ hội đang mở", body["message"])
        status, body = self.get("/api/opportunities", "nhanvien1", {"customer_id": self.customer("anh_duong")})
        self.assertEqual(body["total"], 2)

    def test_ngay_chot_khong_duoc_o_qua_khu_khi_tao_moi(self):
        """Tiêu chí 4: ngày dự kiến chốt không được ở quá khứ khi tạo mới."""
        body = self.make_opp(expect=422, expected_close_date="2026-10-18")
        self.assertFieldError(body, "expected_close_date", "không được ở quá khứ")
        self.make_opp(expected_close_date="2026-10-19")
        opp = self.make_opp(expected_close_date="30/11/2026")
        self.assertEqual(opp["expected_close_date"], "2026-11-30")

    def test_thieu_truong_bat_buoc_bao_loi_tieng_viet(self):
        status, body = self.post("/api/opportunities", "nhanvien1", {})
        self.assertEqual(status, 422)
        messages = [e["message"] for e in body["errors"]]
        self.assertIn("Tên cơ hội là bắt buộc.", messages)
        self.assertIn("Khách hàng là bắt buộc.", messages)
        self.assertIn("Ngày dự kiến chốt là bắt buộc.", messages)
        body = self.make_opp(expect=422, source="facebook", estimated_value=-5)
        self.assertFieldError(body, "source", "Giá trị cho phép")
        self.assertFieldError(body, "estimated_value", "lớn hơn hoặc bằng 0")

    def test_nguoi_lien_he_phai_thuoc_khach_hang(self):
        body = self.make_opp(expect=422, primary_contact_id=self.contact("Bùi Văn Khoa"))
        self.assertFieldError(body, "primary_contact_id", "không thuộc khách hàng")

    def test_khong_tao_o_giai_doan_da_dong(self):
        body = self.make_opp(expect=422, stage_id=self.stage("won"))
        self.assertFieldError(body, "stage_id", "đã đóng")

    def test_pham_vi_quyen_theo_vai_tro(self):
        """Nhân viên chỉ thấy của mình, trưởng nhóm thấy cả nhóm, giám đốc thấy tất cả (SCRUM-29)."""
        body = self.make_opp(user="nhanvien1", expect=422, customer_id=self.customer("an_khang"),
                             primary_contact_id=None)
        self.assertFieldError(body, "customer_id", "không có quyền")
        opp = self.make_opp()
        url = f"/api/opportunities/{opp['id']}"
        self.assertEqual(self.get(url, "nhanvien2")[0], 404)
        self.assertEqual(self.get(url, "truongnhom2")[0], 404)
        self.assertEqual(self.get(url, "truongnhom1")[0], 200)
        self.assertEqual(self.get(url, "giamdoc")[0], 200)
        self.assertEqual(self.get("/api/opportunities", "nhanvien2")[1]["total"], 0)

    def test_giao_co_hoi_cho_nguoi_khac(self):
        status, body = self.post("/api/opportunities", "nhanvien1", {
            "name": "X", "customer_id": self.customer("anh_duong"), "expected_close_date": "2026-11-30",
            "owner_id": self.uid("nhanvien2")})
        self.assertEqual(status, 403)
        opp = self.make_opp(user="truongnhom1", customer_id=self.customer("minh_tri"),
                            primary_contact_id=self.contact("Lý Thanh Tâm"), owner_id=self.uid("nhanvien2"))
        self.assertEqual(opp["owner"]["id"], self.uid("nhanvien2"))
        self.make_opp(user="truongnhom1", expect=403, customer_id=self.customer("minh_tri"),
                      primary_contact_id=None, owner_id=self.uid("nhanvien3"))

    def test_cap_nhat_va_khong_doi_giai_doan_qua_patch(self):
        opp = self.make_opp()
        url = f"/api/opportunities/{opp['id']}"
        status, body = self.patch(url, "nhanvien1", {"stage_id": self.stage("won")})
        self.assertEqual(status, 422)
        self.assertIn("chuyển giai đoạn", body["detail"])
        status, body = self.patch(url, "nhanvien1", {"name": "Tên mới", "estimated_value": 80_000_000,
                                                     "primary_contact_id": self.contact("Ngô Thị Lan")})
        self.assertEqual(status, 200, body)
        self.assertEqual(body["opportunity"]["name"], "Tên mới")
        self.assertEqual(body["opportunity"]["amount"], 80_000_000)
        self.assertEqual(body["opportunity"]["primary_contact"]["full_name"], "Ngô Thị Lan")
        self.assertIn("Đã cập nhật cơ hội", body["message"])

    def test_xoa_co_hoi(self):
        opp = self.make_opp()
        status, body = self.delete(f"/api/opportunities/{opp['id']}", "nhanvien1")
        self.assertEqual(status, 200)
        self.assertIn("Đã xoá cơ hội", body["message"])
        self.assertEqual(self.get(f"/api/opportunities/{opp['id']}", "nhanvien1")[0], 404)

    def test_tim_kiem_va_loc(self):
        self.make_opp(name="Triển khai phần mềm kho")
        self.make_opp(name="Bảo trì máy chủ")
        status, body = self.get("/api/opportunities", "nhanvien1", {"q": "trien khai"})
        self.assertEqual([o["name"] for o in body["items"]], ["Triển khai phần mềm kho"])
        status, body = self.get("/api/opportunities", "nhanvien1", {"status": "won"})
        self.assertEqual(body["total"], 0)
