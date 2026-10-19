"""SCRUM-100 – Tạo và theo dõi công việc có hạn hoàn thành."""
from datetime import datetime

from tests.base import CRMTestCase


class TestScrum100CongViec(CRMTestCase):
    def create(self, user="nhanvien1", expect=201, **payload):
        data = {"title": "Gửi báo giá cho khách", "due_date": "2026-10-23", "priority": "high",
                "customer_id": self.customer("anh_duong")}
        data.update(payload)
        status, body = self.post("/api/tasks", user, data)
        self.assertEqual(status, expect, body)
        return body["task"] if status == 201 else body

    def test_cong_viec_co_tieu_de_han_uu_tien_nguoi_thuc_hien_va_lien_ket(self):
        """Tiêu chí 1."""
        opp = self.make_opp()
        status, body = self.post("/api/tasks", "nhanvien1", {
            "title": "Gửi báo giá cho khách", "due_date": "2026-10-23", "priority": "high",
            "opportunity_id": opp["id"]})
        self.assertEqual(status, 201, body)
        task = body["task"]
        self.assertEqual(task["due_date_display"], "Thứ Sáu 23/10/2026")
        self.assertEqual((task["priority_label"], task["status_label"]), ("Cao", "Chưa hoàn thành"))
        self.assertEqual(task["assignee"]["full_name"], "Lê Văn Cường")
        self.assertEqual(task["customer"]["name"], "Công ty CP Công nghệ Ánh Dương")
        self.assertEqual(task["opportunity"]["id"], opp["id"])
        self.assertEqual(task["due_state_label"], "Còn 4 ngày")
        self.assertIn("Thứ Sáu 23/10/2026", body["message"])

    def test_bat_buoc_gan_khach_hang_hoac_co_hoi_va_han_hop_le(self):
        body = self.create(expect=422, customer_id=None)
        self.assertFieldError(body, "customer_id", "phải gắn với một khách hàng hoặc một cơ hội")
        body = self.create(expect=422, due_date="2026-10-18")
        self.assertFieldError(body, "due_date", "không được ở quá khứ")
        body = self.create(expect=422, title="", priority="gap")
        self.assertFieldError(body, "title", "không được để trống")
        self.assertFieldError(body, "priority", "urgent (Khẩn cấp)")

    def test_danh_dau_hoan_thanh(self):
        """Tiêu chí 2: đánh dấu hoàn thành."""
        task = self.create()
        status, body = self.post(f"/api/tasks/{task['id']}/complete", "nhanvien1", {"note": "Đã gửi email."})
        self.assertEqual(status, 200)
        self.assertEqual((body["task"]["status"], body["task"]["completion_note"]), ("done", "Đã gửi email."))
        self.assertIn("đúng hạn", body["message"])
        self.assertEqual(self.post(f"/api/tasks/{task['id']}/complete", "nhanvien1")[0], 409)
        status, body = self.post(f"/api/tasks/{task['id']}/reopen", "nhanvien1")
        self.assertEqual((status, body["task"]["status"]), (200, "open"))

    def test_hoan_kem_ly_do(self):
        """Tiêu chí 2: hoãn kèm lý do, lưu lịch sử hoãn."""
        task = self.create()
        url = f"/api/tasks/{task['id']}/postpone"
        status, body = self.post(url, "nhanvien1", {"new_due_date": "2026-10-27"})
        self.assertEqual(status, 422)
        self.assertFieldError(body, "reason", "Lý do hoãn là bắt buộc.")
        status, body = self.post(url, "nhanvien1", {"new_due_date": "2026-10-27", "reason": "ok"})
        self.assertFieldError(body, "reason", "ít nhất 5 ký tự")
        status, body = self.post(url, "nhanvien1", {"new_due_date": "2026-10-22", "reason": "Khách đổi lịch"})
        self.assertFieldError(body, "new_due_date", "phải sau hạn hiện tại")
        status, body = self.post(url, "nhanvien1", {"new_due_date": "2026-10-27", "reason": "Khách đi công tác"})
        self.assertEqual(status, 200, body)
        self.assertEqual((body["task"]["due_date"], body["task"]["postpone_count"]), ("2026-10-27", 1))
        self.assertEqual(body["task"]["last_postpone_reason"], "Khách đi công tác")
        self.assertIn("từ 23/10/2026 sang Thứ Ba 27/10/2026", body["message"])
        detail = self.get(f"/api/tasks/{task['id']}", "nhanvien1")[1]
        self.assertEqual(detail["postponements"][0]["old_due_date"], "2026-10-23")
        status, body = self.patch(f"/api/tasks/{task['id']}", "nhanvien1", {"due_date": "2026-11-05"})
        self.assertEqual(status, 422)
        self.assertIn("dùng chức năng Hoãn", body["detail"])
        self.post(f"/api/tasks/{task['id']}/complete", "nhanvien1")
        self.assertEqual(self.post(url, "nhanvien1", {"new_due_date": "2026-11-05", "reason": "Lý do bất kỳ"})[0], 409)

    def test_truong_nhom_giao_viec_cho_thanh_vien_trong_nhom(self):
        """Tiêu chí 3: trưởng nhóm giao việc được cho thành viên trong nhóm."""
        task = self.create(user="truongnhom1", assignee_id=self.uid("nhanvien2"),
                           customer_id=self.customer("an_khang"))
        self.assertEqual(task["assignee"]["full_name"], "Phạm Thị Dung")
        body = self.create(user="truongnhom1", expect=403, assignee_id=self.uid("nhanvien3"),
                           customer_id=self.customer("minh_tri"))
        self.assertIn("thành viên trong nhóm", body["detail"])
        body = self.create(user="nhanvien1", expect=403, assignee_id=self.uid("nhanvien2"))
        self.assertIn("chỉ được tạo công việc cho chính mình", body["detail"])
        self.create(user="giamdoc", assignee_id=self.uid("nhanvien3"), customer_id=self.customer("sao_viet"))
        status, body = self.post(f"/api/tasks/{task['id']}/assign", "truongnhom1",
                                 {"assignee_id": self.uid("nhanvien1")})
        self.assertEqual(status, 200)
        self.assertEqual(body["task"]["assignee"]["full_name"], "Lê Văn Cường")
        self.assertEqual(self.post(f"/api/tasks/{task['id']}/assign", "nhanvien1",
                                   {"assignee_id": self.uid("nhanvien2")})[0], 403)
        status, body = self.patch(f"/api/tasks/{task['id']}", "truongnhom1", {"assignee_id": self.uid("nhanvien2")})
        self.assertEqual(status, 422)

    def test_theo_doi_qua_han_va_nhac_viec(self):
        self.create(title="Gọi lại khách", due_date="2026-10-20")
        self.create(title="Gửi báo giá thứ Sáu", due_date="2026-10-23")
        self.at(datetime(2026, 10, 22, 8, 0))
        body = self.get("/api/tasks/reminders", "nhanvien1")[1]
        self.assertEqual(body["message"], "Bạn có 1 công việc quá hạn, 1 công việc đến hạn ngày mai.")
        self.assertEqual(body["overdue"][0]["due_state_label"], "Quá hạn 2 ngày")
        body = self.get("/api/tasks", "nhanvien1", {"due": "overdue"})[1]
        self.assertEqual([t["title"] for t in body["items"]], ["Gọi lại khách"])
        self.assertTrue(body["items"][0]["is_overdue"])
        body = self.get("/api/tasks", "nhanvien1", {"due": "next_7_days"})[1]
        self.assertEqual(body["total"], 1)

    def test_pham_vi_xem_cong_viec(self):
        task = self.create()
        self.assertEqual(self.get(f"/api/tasks/{task['id']}", "nhanvien2")[0], 404)
        self.assertEqual(self.get(f"/api/tasks/{task['id']}", "truongnhom1")[0], 200)
        self.assertEqual(self.get(f"/api/tasks/{task['id']}", "truongnhom2")[0], 404)
        assigned = self.create(user="truongnhom1", assignee_id=self.uid("nhanvien2"),
                               customer_id=self.customer("an_khang"))
        body = self.get("/api/tasks", "nhanvien2", {"assigned_to_me": "true"})[1]
        self.assertEqual([t["id"] for t in body["items"]], [assigned["id"]])
        self.assertEqual(self.delete(f"/api/tasks/{assigned['id']}", "nhanvien2")[0], 403)
        self.assertEqual(self.delete(f"/api/tasks/{assigned['id']}", "truongnhom1")[0], 200)
