"""SCRUM-99 – Ghi nhận hoạt động với khách hàng."""
from datetime import datetime

from tests.base import CRMTestCase


class TestScrum99HoatDong(CRMTestCase):
    def setUp(self):
        super().setUp()
        self.opp = self.make_opp()

    def create(self, user="nhanvien1", expect=201, **payload):
        status, body = self.post("/api/activities", user, payload)
        self.assertEqual(status, expect, body)
        return body

    def test_bon_loai_hoat_dong(self):
        """Tiêu chí 1: cuộc gọi, cuộc gặp, email, ghi chú."""
        labels = []
        for kind in ("call", "meeting", "email", "note"):
            body = self.create(activity_type=kind, customer_id=self.customer("anh_duong"), content="Nội dung.")
            labels.append(body["activity"]["activity_type_label"])
        self.assertEqual(labels, ["Cuộc gọi", "Cuộc gặp", "Email", "Ghi chú"])
        body = self.create(expect=422, activity_type="sms", customer_id=self.customer("anh_duong"), content="x")
        self.assertFieldError(body, "activity_type", "call (Cuộc gọi)")

    def test_gan_khach_hang_nguoi_lien_he_va_co_hoi(self):
        """Tiêu chí 2: gắn với khách hàng, người liên hệ và cơ hội; tự suy ra khách hàng."""
        activity = self.create(activity_type="call", opportunity_id=self.opp["id"],
                               contact_id=self.contact("Ngô Thị Lan"), content="Gọi xác nhận lịch.")["activity"]
        self.assertEqual(activity["customer"]["name"], "Công ty CP Công nghệ Ánh Dương")
        self.assertEqual(activity["contact"]["full_name"], "Ngô Thị Lan")
        self.assertEqual(activity["opportunity"]["id"], self.opp["id"])
        activity = self.create(activity_type="email", contact_id=self.contact("Bùi Văn Khoa"),
                               content="Gửi tài liệu.")["activity"]
        self.assertEqual(activity["customer"]["name"], "Công ty TNHH Thương mại Hưng Thịnh")
        body = self.create(expect=422, activity_type="call", customer_id=self.customer("hung_thinh"),
                           opportunity_id=self.opp["id"], content="x")
        self.assertFieldError(body, "opportunity_id", "không thuộc khách hàng")
        body = self.create(expect=422, activity_type="call", opportunity_id=self.opp["id"],
                           contact_id=self.contact("Bùi Văn Khoa"), content="x")
        self.assertFieldError(body, "contact_id", "không thuộc khách hàng")
        body = self.create(expect=422, activity_type="call", content="x")
        self.assertFieldError(body, "customer_id", "Vui lòng chọn khách hàng")

    def test_ghi_thoi_diem_thoi_luong_noi_dung_ket_qua(self):
        """Tiêu chí 3."""
        activity = self.create(activity_type="meeting", opportunity_id=self.opp["id"],
                               occurred_at="2026-10-19T08:00:00+07:00", duration_minutes=45,
                               content="Trình bày demo.", outcome="Khách hẹn chốt tuần sau.")["activity"]
        self.assertEqual(activity["occurred_at"], "2026-10-19T08:00:00")
        self.assertEqual(activity["occurred_at_display"], "19/10/2026 08:00")
        self.assertEqual((activity["duration_minutes"], activity["content"], activity["outcome"]),
                         (45, "Trình bày demo.", "Khách hẹn chốt tuần sau."))
        activity = self.create(activity_type="call", customer_id=self.customer("anh_duong"),
                               occurred_at="2026-10-19T00:30:00Z", content="Gọi từ nước ngoài.")["activity"]
        self.assertEqual(activity["occurred_at"], "2026-10-19T07:30:00")
        body = self.create(expect=422, activity_type="call", customer_id=self.customer("anh_duong"),
                           content="x", duration_minutes=1500)
        self.assertFieldError(body, "duration_minutes", "không được lớn hơn 1440")
        body = self.create(expect=422, activity_type="meeting", customer_id=self.customer("anh_duong"))
        self.assertFieldError(body, "content", "nội dung trao đổi")

    def test_ghi_bu_qua_khu_va_len_lich_tuong_lai(self):
        """Tiêu chí 4: ghi được hoạt động đã diễn ra trong quá khứ, không chỉ hoạt động sắp tới."""
        past = self.create(activity_type="meeting", customer_id=self.customer("anh_duong"),
                           occurred_at="16/10/2026 14:00", content="Gặp tuần trước.")["activity"]
        self.assertEqual((past["status"], past["status_label"]), ("completed", "Đã diễn ra"))
        self.assertEqual(past["created_at"], "2026-10-19T09:00:00")
        future = self.create(activity_type="meeting", opportunity_id=self.opp["id"],
                             occurred_at="2026-10-22T10:00:00", subject="Demo sản phẩm")
        self.assertEqual(future["activity"]["status_label"], "Sắp diễn ra")
        self.assertIn("Đã lên lịch cuộc gặp", future["message"])
        body = self.create(expect=422, activity_type="note", customer_id=self.customer("anh_duong"),
                           occurred_at="2026-10-22T10:00:00", content="x")
        self.assertIn("không thể lên lịch trước", body["detail"])
        body = self.create(expect=422, activity_type="call", customer_id=self.customer("anh_duong"),
                           occurred_at="2026-10-22T10:00:00", status="completed", content="x")
        self.assertIn("không thể có thời điểm ở tương lai", body["detail"])

    def test_ghi_nhanh_tren_dien_thoai(self):
        """Tiêu chí 5: dùng nhanh trên điện thoại ngay sau khi rời văn phòng khách."""
        status, body = self.post("/api/activities/quick", "nhanvien1", {
            "opportunity_id": self.opp["id"], "content": "Khách đồng ý phương án.", "outcome": "Hẹn gửi báo giá.",
            "duration_minutes": 60, "ended_minutes_ago": 10,
            "follow_up_task": {"title": "Gửi báo giá cho khách", "due_date": "2026-10-23", "priority": "high"}})
        self.assertEqual(status, 201, body)
        activity = body["activity"]
        self.assertEqual(activity["activity_type"], "meeting")
        self.assertEqual(activity["occurred_at"], "2026-10-19T07:50:00")  # 9:00 − 10 phút − 60 phút
        self.assertEqual(activity["logged_via_label"], "Điện thoại (ghi nhanh)")
        self.assertEqual(body["follow_up_task"]["due_date_display"], "Thứ Sáu 23/10/2026")
        self.assertEqual(body["follow_up_task"]["opportunity"]["id"], self.opp["id"])
        self.assertIn("Đã tạo công việc tiếp theo", body["message"])

    def test_ghi_nhanh_loi_cong_viec_tiep_theo_thi_khong_luu_gi(self):
        status, body = self.post("/api/activities/quick", "nhanvien1", {
            "opportunity_id": self.opp["id"], "content": "Gặp khách.",
            "follow_up_task": {"title": "Gửi báo giá", "due_date": "2026-10-01"}})
        self.assertEqual(status, 422)
        self.assertFieldError(body, "follow_up_task.due_date", "không được ở quá khứ")
        self.assertEqual(self.get("/api/activities", "nhanvien1")[1]["total"], 0)

    def test_goi_y_cho_man_hinh_ghi_nhanh_va_cap_nhat_ket_qua(self):
        planned = self.create(activity_type="meeting", opportunity_id=self.opp["id"],
                              occurred_at="2026-10-19T14:00:00", subject="Họp chốt phạm vi")["activity"]
        body = self.get("/api/activities/quick-suggestions", "nhanvien1")[1]
        self.assertEqual([a["id"] for a in body["needs_result"]], [planned["id"]])
        self.assertEqual(body["needs_result"][0]["time_display"], "14:00")
        self.assertEqual(body["open_opportunities"][0]["id"], self.opp["id"])
        self.assertIn("Công ty CP Công nghệ Ánh Dương", [c["name"] for c in body["recent_customers"]])

        self.at(datetime(2026, 10, 19, 16, 0))
        status, body = self.post(f"/api/activities/{planned['id']}/complete", "nhanvien1",
                                 {"content": "Đã chốt phạm vi.", "outcome": "Khách ký biên bản.", "duration_minutes": 90})
        self.assertEqual(status, 200, body)
        self.assertEqual((body["activity"]["status"], body["activity"]["occurred_at"]),
                         ("completed", "2026-10-19T14:00:00"))
        self.assertEqual(self.post(f"/api/activities/{planned['id']}/complete", "nhanvien1", {})[0], 409)

    def test_lich_su_trao_doi_dung_chung(self):
        """Lịch sử với khách không nằm trong hộp thư riêng: đồng nghiệp/trưởng nhóm ghi vẫn hiện chung."""
        self.create(activity_type="call", customer_id=self.customer("anh_duong"), content="Nhân viên gọi.")
        self.create(user="truongnhom1", activity_type="meeting", customer_id=self.customer("anh_duong"),
                    content="Trưởng nhóm gặp giám đốc khách.")
        status, body = self.get(f"/api/customers/{self.customer('anh_duong')}/activities", "nhanvien1")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 2)
        self.assertEqual({a["owner"]["full_name"] for a in body["items"]}, {"Lê Văn Cường", "Trần Thị Bình"})
        self.assertEqual({t["label"]: t["count"] for t in body["summary"]["by_type"]}["Cuộc gặp"], 1)
        self.assertEqual(self.get(f"/api/customers/{self.customer('anh_duong')}/activities", "nhanvien2")[0], 404)

    def test_pham_vi_va_quyen_sua(self):
        body = self.create(user="nhanvien2", expect=422, activity_type="call",
                           customer_id=self.customer("anh_duong"), content="x")
        self.assertFieldError(body, "customer_id", "không có quyền")
        mine = self.create(activity_type="call", customer_id=self.customer("anh_duong"), content="Gọi.")["activity"]
        lead = self.create(user="truongnhom1", activity_type="note", customer_id=self.customer("anh_duong"),
                           content="Ghi chú của trưởng nhóm.")["activity"]
        self.assertEqual(self.get(f"/api/activities/{mine['id']}", "nhanvien2")[0], 404)
        status, body = self.patch(f"/api/activities/{lead['id']}", "nhanvien1", {"content": "Sửa"})
        self.assertEqual(status, 403)
        status, body = self.patch(f"/api/activities/{mine['id']}", "truongnhom1", {"outcome": "Đã bổ sung."})
        self.assertEqual(status, 200, body)
        self.assertEqual(self.delete(f"/api/activities/{mine['id']}", "nhanvien1")[0], 200)

    def test_loc_danh_sach(self):
        self.create(activity_type="call", customer_id=self.customer("anh_duong"), content="Gọi báo giá.",
                    occurred_at="2026-10-10T09:00:00")
        self.create(activity_type="meeting", opportunity_id=self.opp["id"], content="Gặp demo.")
        body = self.get("/api/activities", "nhanvien1", {"activity_type": "meeting"})[1]
        self.assertEqual(body["total"], 1)
        body = self.get("/api/activities", "nhanvien1", {"date_from": "2026-10-01", "date_to": "2026-10-15"})[1]
        self.assertEqual(body["total"], 1)
        body = self.get("/api/activities", "nhanvien1", {"q": "bao gia"})[1]
        self.assertEqual(body["total"], 1)
