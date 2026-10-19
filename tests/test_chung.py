"""Kiểm thử chung: đăng nhập, thông báo lỗi tiếng Việt, danh mục API, dữ liệu mẫu."""
from app import seed
from app.db import commit, scalar
from tests.base import CRMTestCase


class TestChung(CRMTestCase):
    def test_dang_nhap_thanh_cong_va_that_bai(self):
        status, body = self.call("POST", "/api/auth/login", json={"username": "nhanvien1", "password": "123456"})
        self.assertEqual(status, 200)
        self.assertIn("Đăng nhập thành công", body["message"])
        self.assertEqual(body["user"]["role_label"], "Nhân viên kinh doanh")
        status, body = self.call("POST", "/api/auth/login", json={"username": "nhanvien1", "password": "sai"})
        self.assertEqual(status, 401)
        self.assertEqual(body["detail"], "Tên đăng nhập hoặc mật khẩu không đúng.")

    def test_chua_dang_nhap_va_token_sai(self):
        status, body = self.call("GET", "/api/opportunities")
        self.assertEqual(status, 401)
        self.assertIn("Bạn chưa đăng nhập", body["detail"])
        response = self.client.get("/api/opportunities", headers={"Authorization": "Bearer abc"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["detail"], "Token đăng nhập không hợp lệ.")

    def test_loi_he_thong_bang_tieng_viet(self):
        status, body = self.get("/api/khong-co", "nhanvien1")
        self.assertEqual(status, 404)
        self.assertIn("Không tìm thấy đường dẫn API", body["detail"])
        status, body = self.call("PUT", "/api/opportunities", "nhanvien1", json={})
        self.assertEqual(status, 405)
        self.assertIn("không được hỗ trợ", body["detail"])
        response = self.client.post("/api/opportunities", data="{sai json",
                                    headers={"Authorization": f"Bearer {self.tokens['nhanvien1']}",
                                             "Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["detail"], "Dữ liệu gửi lên không phải JSON hợp lệ.")

    def test_json_utf8_giu_nguyen_dau(self):
        response = self.client.post("/api/auth/login", json={"username": "giamdoc", "password": "123456"})
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=utf-8")
        self.assertIn("Nguyễn Văn An".encode("utf-8"), response.data)

    def test_danh_muc_api_va_nhan_tieng_viet(self):
        status, body = self.get("/api", None)
        self.assertEqual(status, 200)
        paths = {e["path"] for e in body["endpoints"]}
        for path in ("/api/opportunities", "/api/pipeline/board", "/api/opportunities/<int:opp_id>/lines",
                     "/api/stage-rules", "/api/activities/quick", "/api/tasks/<int:task_id>/postpone"):
            self.assertIn(path, paths)
        status, body = self.get("/api/lookups/enums", "nhanvien1")
        self.assertEqual(status, 200)
        self.assertIn({"value": "meeting", "label": "Cuộc gặp"}, body["activity_types"])

    def test_tra_cuu_khach_hang_khong_phan_biet_dau(self):
        status, body = self.get("/api/lookups/customers", "nhanvien1", {"q": "anh duong"})
        self.assertEqual(status, 200)
        self.assertEqual([c["name"] for c in body["items"]], ["Công ty CP Công nghệ Ánh Dương"])

    def test_du_lieu_mau_day_du(self):
        with self.app.app_context():
            from app.db import drop_all, init_db
            drop_all()
            init_db()
            seed.seed_all()
            commit()
            self.assertEqual(scalar("SELECT COUNT(*) FROM opportunities"), 8)
            self.assertEqual(scalar("SELECT COUNT(*) FROM stage_exit_rules"), 3)
            self.assertEqual(scalar("SELECT COUNT(*) FROM opportunity_stage_history WHERE is_override = 1"), 1)
            self.assertGreaterEqual(scalar("SELECT COUNT(*) FROM tasks"), 6)
