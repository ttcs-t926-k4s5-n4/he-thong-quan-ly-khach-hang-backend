"""Kiểm thử QA toàn diện: Đăng nhập, Phiên, RBAC (Data Scope), Tính toàn vẹn Transaction & Đối chiếu CSDL."""
from datetime import datetime, timedelta
import unittest

from app import clock
from app.auth import _serializer, create_token
from app.db import commit, execute, row, rows, scalar
from tests.base import CRMTestCase, NOW


class TestQAToanDienBackend(CRMTestCase):
    # =========================================================================
    # 1. ĐĂNG NHẬP, ĐĂNG XUẤT, PHIÊN LÀM VIỆC & BẢO MẬT XÁC THỰC
    # =========================================================================
    def test_01_dang_nhap_tat_ca_cac_vai_tro_he_thong(self):
        """Kiểm thử đăng nhập thành công cho cả 7 tài khoản thuộc mọi cấp bậc trong hệ thống."""
        danh_sach_tai_khoan = [
            ("giamdoc", "director", "Giám đốc kinh doanh", None),
            ("truongnhom1", "team_lead", "Trưởng nhóm", "Nhóm Kinh doanh Miền Bắc"),
            ("nhanvien1", "staff", "Nhân viên kinh doanh", "Nhóm Kinh doanh Miền Bắc"),
            ("nhanvien2", "staff", "Nhân viên kinh doanh", "Nhóm Kinh doanh Miền Bắc"),
            ("truongnhom2", "team_lead", "Trưởng nhóm", "Nhóm Kinh doanh Miền Nam"),
            ("nhanvien3", "staff", "Nhân viên kinh doanh", "Nhóm Kinh doanh Miền Nam"),
            ("quantri", "admin", "Quản trị hệ thống", None),
        ]
        for username, exp_role, exp_role_label, exp_team_name in danh_sach_tai_khoan:
            status, body = self.call("POST", "/api/auth/login", json={"username": username, "password": "123456"})
            self.assertEqual(status, 200, f"Đăng nhập thất bại cho {username}: {body}")
            self.assertIn("access_token", body)
            self.assertEqual(body["token_type"], "Bearer")
            self.assertEqual(body["expires_in"], 28800)
            user = body["user"]
            self.assertEqual(user["username"], username)
            self.assertEqual(user["role"], exp_role)
            self.assertEqual(user["role_label"], exp_role_label)
            if exp_team_name:
                self.assertIsNotNone(user["team"])
                self.assertEqual(user["team"]["name"], exp_team_name)

    def test_02_dang_nhap_sai_mat_khau_va_tai_khoan_khong_ton_tai(self):
        """Đăng nhập sai mật khẩu hoặc tài khoản không tồn tại phải trả về 401 cùng thông điệp bảo mật."""
        # Sai mật khẩu
        status, body = self.call("POST", "/api/auth/login", json={"username": "nhanvien1", "password": "SaiMatKhau@123"})
        self.assertEqual(status, 401)
        self.assertEqual(body["detail"], "Tên đăng nhập hoặc mật khẩu không đúng.")

        # Tài khoản không tồn tại
        status, body = self.call("POST", "/api/auth/login", json={"username": "user_khong_ton_tai", "password": "123456"})
        self.assertEqual(status, 401)
        self.assertEqual(body["detail"], "Tên đăng nhập hoặc mật khẩu không đúng.")

    def test_03_dang_nhap_chong_sql_injection(self):
        """Kiểm tra tấn công SQL Injection trong trường đăng nhập."""
        payloads = [
            {"username": "' OR '1'='1", "password": "123456"},
            {"username": "admin' --", "password": "any"},
            {"username": "nhanvien1", "password": "' OR '1'='1"},
        ]
        for p in payloads:
            status, body = self.call("POST", "/api/auth/login", json=p)
            self.assertEqual(status, 401, f"SQLi payload không bị từ chối: {p}")

    def test_04_tai_khoan_bi_khoa_khong_the_dang_nhap(self):
        """Tài khoản bị khóa (is_active = 0) bị chặn đăng nhập và trả thông báo rõ ràng."""
        with self.app.app_context():
            execute("UPDATE users SET is_active = 0 WHERE username = 'nhanvien3'")
            commit()

        status, body = self.call("POST", "/api/auth/login", json={"username": "nhanvien3", "password": "123456"})
        self.assertEqual(status, 401)
        self.assertIn("Tài khoản đã bị khoá", body["detail"])

    def test_05_token_bi_vo_hieu_khi_tai_khoan_bi_khoa_giua_phien(self):
        """Người dùng đã đăng nhập lấy token, sau đó tài khoản bị khóa -> các API tiếp theo phải từ chối."""
        token_nhanvien2 = self.tokens["nhanvien2"]
        # Khi đang active gọi được
        res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_nhanvien2}"})
        self.assertEqual(res.status_code, 200)

        # Khóa tài khoản
        with self.app.app_context():
            execute("UPDATE users SET is_active = 0 WHERE username = 'nhanvien2'")
            commit()

        # Gọi lại API với token cũ
        res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_nhanvien2}"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("đã bị khoá", res.get_json()["detail"])

    def test_06_token_gia_mao_hoac_sai_chu_ky(self):
        """Token rác hoặc bị sửa đổi payload bị từ chối với mã lỗi 401."""
        tampered_token = self.tokens["nhanvien1"] + "invalid_signature"
        res = self.client.get("/api/opportunities", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["detail"], "Token đăng nhập không hợp lệ.")

    def test_07_token_het_han_thoi_gian(self):
        """Token hết hạn (quá TOKEN_MAX_AGE_SECONDS) bị từ chối và yêu cầu đăng nhập lại."""
        # Đặt thời hạn token âm để kiểm thử phát hiện hết hạn
        self.app.config["TOKEN_MAX_AGE_SECONDS"] = -1
        token = self.tokens["nhanvien1"]
        res = self.client.get("/api/opportunities", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Phiên đăng nhập đã hết hạn", res.get_json()["detail"])

    def test_08_kiem_tra_endpoint_dang_xuat(self):
        """Ghi nhận kiến trúc: Hệ thống sử dụng Stateless JWT/Signed Token; không có endpoint /api/auth/logout."""
        status, _ = self.call("POST", "/api/auth/logout", "nhanvien1")
        self.assertEqual(status, 404, "Endpoint logout không nằm trong danh mục REST API (stateless Bearer token).")

    # =========================================================================
    # 2. PHÂN QUYỀN TRUY CẬP DỮ LIỆU (DATA SCOPE: CỦA TÔI / NHÓM / TOÀN BỘ)
    # =========================================================================
    def test_09_data_scope_co_hoi_ban_hang_truy_cap_truc_tiep_api(self):
        """Kiểm tra quyền truy cập cơ hội theo vai trò qua API trực tiếp."""
        # nhanvien1 (Miền Bắc) tạo cơ hội
        opp = self.make_opp(user="nhanvien1", name="Cơ hội riêng của NV1")
        opp_id = opp["id"]
        url = f"/api/opportunities/{opp_id}"

        # 1. Chính chủ nhanvien1 xem được
        status, body = self.get(url, "nhanvien1")
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], opp_id)

        # 2. nhanvien2 (cùng nhóm Miền Bắc) truy cập trực tiếp URL ID -> 404 (bị ẩn để bảo vệ dữ liệu cá nhân)
        status, _ = self.get(url, "nhanvien2")
        self.assertEqual(status, 404)

        # 3. nhanvien3 (khác nhóm - Miền Nam) truy cập trực tiếp -> 404
        status, _ = self.get(url, "nhanvien3")
        self.assertEqual(status, 404)

        # 4. truongnhom1 (Trưởng nhóm Miền Bắc) xem được cơ hội của thành viên trong nhóm
        status, body = self.get(url, "truongnhom1")
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], opp_id)

        # 5. truongnhom2 (Trưởng nhóm Miền Nam) truy cập trực tiếp cơ hội nhóm Miền Bắc -> 404
        status, _ = self.get(url, "truongnhom2")
        self.assertEqual(status, 404)

        # 6. giamdoc & quantri xem được toàn bộ
        self.assertEqual(self.get(url, "giamdoc")[0], 200)
        self.assertEqual(self.get(url, "quantri")[0], 200)

    def test_10_data_scope_sua_co_hoi_khong_phai_cua_minh(self):
        """Nhân viên không được sửa cơ hội của nhân viên khác kể cả cùng nhóm."""
        opp = self.make_opp(user="nhanvien1")
        url = f"/api/opportunities/{opp['id']}"

        # nhanvien2 sửa cơ hội của nhanvien1 -> 404
        status, _ = self.patch(url, "nhanvien2", {"name": "Tên đã bị hack"})
        self.assertEqual(status, 404)

        # Kiểm tra database tên cơ hội không bị đổi
        with self.app.app_context():
            ten_thuc_te = scalar("SELECT name FROM opportunities WHERE id = ?", (opp["id"],))
            self.assertEqual(ten_thuc_te, opp["name"])

    def test_11_data_scope_danh_sach_co_hoi_theo_tung_vai_tro(self):
        """Kiểm tra danh sách cơ hội trả về đúng phạm vi từng vai trò."""
        # nhanvien1 tạo 1 cơ hội
        self.make_opp(user="nhanvien1", customer_id=self.customer("anh_duong"),
                      primary_contact_id=self.contact("Đỗ Minh Hải"), name="Cơ hội Miền Bắc")
        # Tạo thêm cơ hội cho nhanvien3 (Miền Nam)
        self.make_opp(user="nhanvien3", customer_id=self.customer("sao_viet"),
                      primary_contact_id=self.contact("Đặng Hoài Nam"), name="Cơ hội Miền Nam")

        # nhanvien1 chỉ thấy cơ hội của mình
        status, body = self.get("/api/opportunities", "nhanvien1")
        self.assertEqual(status, 200)
        self.assertTrue(all(item["owner"]["id"] == self.uid("nhanvien1") for item in body["items"]))

        # truongnhom1 thấy các cơ hội của nhóm Miền Bắc
        status, body = self.get("/api/opportunities", "truongnhom1")
        self.assertEqual(status, 200)
        owners = {item["owner"]["id"] for item in body["items"]}
        self.assertNotIn(self.uid("nhanvien3"), owners)

        # giamdoc thấy cả Miền Bắc và Miền Nam
        status, body = self.get("/api/opportunities", "giamdoc")
        self.assertEqual(status, 200)
        owners_all = {item["owner"]["id"] for item in body["items"]}
        self.assertIn(self.uid("nhanvien1"), owners_all)
        self.assertIn(self.uid("nhanvien3"), owners_all)

    def test_12_rbac_cau_hinh_stage_gates_va_ghi_de_theo_nhom(self):
        """Chỉ Giám đốc được cấu hình Stage Rules; Trưởng nhóm chỉ được ghi đè cho nhóm mình."""
        # 1. Nhân viên và Trưởng nhóm tạo Stage Rule -> 403 Forbidden
        status, body = self.post("/api/stage-rules", "nhanvien1", {
            "stage_id": self.stage("qualification"), "rule_type": "min_activities", "min_count": 1})
        self.assertEqual(status, 403)

        status, body = self.post("/api/stage-rules", "truongnhom1", {
            "stage_id": self.stage("qualification"), "rule_type": "min_activities", "min_count": 1})
        self.assertEqual(status, 403)

        # 2. Giám đốc tạo rule thành công
        rule = self.add_rule(stage_id=self.stage("prospecting"), rule_type="min_activities",
                             activity_type="meeting", min_count=1)
        self.assertIsNotNone(rule["id"])

        # 3. nhanvien1 cố chuyển giai đoạn khi chưa có cuộc gặp -> 409 Conflict bị chặn
        opp_nv1 = self.make_opp(user="nhanvien1")
        status, body = self.move(opp_nv1["id"], "qualification", user="nhanvien1")
        self.assertEqual(status, 409)
        self.assertIn("Cần ít nhất 1 cuộc gặp", body["detail"])

        # 4. truongnhom2 (khác nhóm) cố ghi đè cơ hội của nhanvien1 -> 404
        status, body = self.move(opp_nv1["id"], "qualification", user="truongnhom2",
                                 override=True, override_reason="Ghi đè trái phép khác nhóm")
        self.assertEqual(status, 404)

        # 5. truongnhom1 (cùng nhóm) ghi đè hợp lệ kèm lý do -> 200 thành công
        status, body = self.move(opp_nv1["id"], "qualification", user="truongnhom1",
                                 override=True, override_reason="Khách hàng VIP đã gặp riêng ngoài giờ")
        self.assertEqual(status, 200)
        self.assertEqual(body["opportunity"]["stage"]["code"], "qualification")

    def test_13_rbac_giao_viec_dung_nhom_va_chan_khac_nhom(self):
        """Trưởng nhóm chỉ được giao việc cho thành viên trong nhóm phụ trách, chặn giao việc ngoài nhóm."""
        # truongnhom1 giao việc cho nhanvien1 (cùng nhóm Miền Bắc) -> 201
        payload = {
            "title": "Chăm sóc khách hàng VIP",
            "due_date": "2026-11-20",
            "priority": "high",
            "assignee_id": self.uid("nhanvien1"),
            "customer_id": self.customer("anh_duong"),
        }
        status, body = self.post("/api/tasks", "truongnhom1", payload)
        self.assertEqual(status, 201)

        # truongnhom1 cố giao việc cho nhanvien3 (Nhóm Miền Nam) -> 403 bị chặn
        payload_ngoai_nhom = dict(payload, assignee_id=self.uid("nhanvien3"))
        status, body = self.post("/api/tasks", "truongnhom1", payload_ngoai_nhom)
        self.assertEqual(status, 403)
        self.assertIn("thành viên trong nhóm", body["detail"])

    # =========================================================================
    # 3. TÍNH TOÀN VẸN DỮ LIỆU & TRANSACTION ROLLBACK KHI THAO TÁC LỖI
    # =========================================================================
    def test_14_toan_ven_du_lieu_ghi_nhanh_hoat_dong_khi_loi_cong_viec(self):
        """Khi ghi nhanh hoạt động kèm công việc tiếp theo: nếu công việc lỗi thì toàn bộ phải rollback, không lưu hoạt động mồ côi."""
        with self.app.app_context():
            so_hd_truoc = scalar("SELECT COUNT(*) FROM activities")
            so_cv_truoc = scalar("SELECT COUNT(*) FROM tasks")

        # Gửi payload có hoạt động hợp lệ nhưng công việc có hạn ở quá khứ
        payload = {
            "activity_type": "call",
            "customer_id": self.customer("anh_duong"),
            "content": "Gọi điện trao đổi nhưng công việc tiếp theo có hạn sai.",
            "duration_minutes": 15,
            "follow_up_task": {
                "title": "Việc cần làm tiếp",
                "due_date": "2026-10-01",  # Quá khứ so với NOW 2026-10-19
            },
        }
        status, body = self.post("/api/activities/quick", "nhanvien1", payload)
        self.assertEqual(status, 422)
        self.assertFieldError(body, "follow_up_task.due_date", "không được ở quá khứ")

        # Kiểm tra tính toàn vẹn trong CSDL: không có bản ghi nào được ghi dở dang
        with self.app.app_context():
            so_hd_sau = scalar("SELECT COUNT(*) FROM activities")
            so_cv_sau = scalar("SELECT COUNT(*) FROM tasks")
            self.assertEqual(so_hd_sau, so_hd_truoc, "Lỗi toàn vẹn: Hoạt động đã bị lưu dù transaction thất bại!")
            self.assertEqual(so_cv_sau, so_cv_truoc, "Lỗi toàn vẹn: Công việc đã bị lưu dở dang!")

    def test_15_toan_ven_du_lieu_chuyen_giai_doan_bi_chan_khong_tao_lich_su(self):
        """Khi chuyển giai đoạn bị chặn do không thoả điều kiện, không sinh bản ghi lịch sử và không đổi stage."""
        self.add_rule(stage_id=self.stage("prospecting"), rule_type="min_activities",
                      activity_type="meeting", min_count=1)
        opp = self.make_opp(user="nhanvien1")

        with self.app.app_context():
            so_ls_truoc = scalar("SELECT COUNT(*) FROM opportunity_stage_history WHERE opportunity_id = ?", (opp["id"],))

        status, body = self.move(opp["id"], "qualification", user="nhanvien1")
        self.assertEqual(status, 409)

        with self.app.app_context():
            stage_hien_tai = scalar("SELECT stage_id FROM opportunities WHERE id = ?", (opp["id"],))
            self.assertEqual(stage_hien_tai, self.stage("prospecting"))
            so_ls_sau = scalar("SELECT COUNT(*) FROM opportunity_stage_history WHERE opportunity_id = ?", (opp["id"],))
            self.assertEqual(so_ls_sau, so_ls_truoc, "Lịch sử giai đoạn bị ghi nhận sai khi thao tác thất bại!")

    # =========================================================================
    # 4. ĐỐI CHIẾU PHẢN HỒI API VỚI DỮ LIỆU THỰC LƯU TRONG DATABASE
    # =========================================================================
    def test_16_doi_chieu_phan_hoi_api_voi_du_lieu_luu_csdl(self):
        """Đối chiếu phản hồi API khi tạo cơ hội và thêm sản phẩm trực tiếp với các bản ghi trong SQLite."""
        opp = self.make_opp(user="nhanvien1", name="Hợp đồng dịch vụ bảo mật", estimated_value=0)
        opp_id = opp["id"]

        # Thêm 2 dòng sản phẩm (DV-TK dịch vụ một lần 15tr, CRM-STD thuê bao 250k)
        status1, body1 = self.post(f"/api/opportunities/{opp_id}/lines", "nhanvien1", {
            "product_id": self.product("DV-TK"), "quantity": 2, "unit_price": 15_000_000, "discount_percent": 10})
        self.assertEqual(status1, 201)
        # Thành tiền: 2 * 15.000.000 * 0.9 = 27.000.000

        status2, body2 = self.post(f"/api/opportunities/{opp_id}/lines", "nhanvien1", {
            "product_id": self.product("CRM-STD"), "quantity": 10, "periods": 12, "unit_price": 250_000, "discount_percent": 0})
        self.assertEqual(status2, 201)
        # Thành tiền thuê bao: 10 * 250.000 * 12 kỳ = 30.000.000
        # Tổng giá trị cơ hội: 27.000.000 + 30.000.000 = 57.000.000

        # Đối chiếu trực tiếp vào SQLite
        with self.app.app_context():
            opp_db = row("SELECT name, estimated_value, amount, amount_source FROM opportunities WHERE id = ?", (opp_id,))
            self.assertIsNotNone(opp_db)
            self.assertEqual(opp_db["name"], "Hợp đồng dịch vụ bảo mật")
            self.assertEqual(opp_db["amount"], 57_000_000)
            self.assertEqual(opp_db["amount_source"], "lines")
            self.assertEqual(opp_db["estimated_value"], 0)

            lines_db = rows("SELECT product_id, quantity, unit_price, discount_percent, line_total "
                            "FROM opportunity_lines WHERE opportunity_id = ? ORDER BY id", (opp_id,))
            self.assertEqual(len(lines_db), 2)
            self.assertEqual(lines_db[0]["line_total"], 27_000_000)
            self.assertEqual(lines_db[1]["line_total"], 30_000_000)

    # =========================================================================
    # 5. TÁI HIỆN BUG & KIỂM THỬ AN TOÀN XÁC THỰC (BUG-QA-002 & S1-02)
    # =========================================================================
    def test_17_tai_hien_bug_qa_002_khoa_tai_khoan_sau_5_lan_sai(self):
        """[BUG-QA-002] Tái hiện lỗi: Nhập sai mật khẩu liên tiếp 5 lần phải khóa tài khoản trong 15 phút.
        Lần thứ 6 dù nhập đúng mật khẩu cũng không được phép cấp quyền đăng nhập (phải trả về mã lỗi và thông báo khóa).
        Ghi nhận FAIL khi backend chưa sửa lỗi (bảng users thiếu cột đếm, login không chặn).
        """
        username = "nhanvien1"

        # Bước 1: Gửi liên tiếp 5 yêu cầu đăng nhập sai mật khẩu
        for i in range(1, 6):
            status, body = self.call("POST", "/api/auth/login", json={"username": username, "password": f"SaiMatKhau@{i}"})
            self.assertEqual(status, 401, f"Lần thử sai thứ {i} phải trả về HTTP 401")
            self.assertEqual(body.get("detail"), "Tên đăng nhập hoặc mật khẩu không đúng.")

        # Bước 2: Lần thứ 6 gửi mật khẩu ĐÚNG ("123456")
        status_6, body_6 = self.call("POST", "/api/auth/login", json={"username": username, "password": "123456"})

        # Kỳ vọng nghiệp vụ: Tài khoản đã bị khóa tạm thời 15 phút, KHÔNG ĐƯỢC trả về 200 kèm access_token.
        self.assertEqual(
            status_6,
            401,
            "Sau 5 lần sai, lần thứ 6 phải bị từ chối với HTTP 401 Unauthorized"
        )
        detail_msg = (body_6.get("detail") or "").lower()
        self.assertTrue(
            "khoá" in detail_msg or "khóa" in detail_msg or "15 phút" in detail_msg,
            f"Thông báo lỗi không chứa nội dung khóa tài khoản 15 phút: {body_6}"
        )

        # Bước 3: Trong thời gian khóa (sau 10 phút), vẫn tiếp tục bị khóa
        clock.freeze(NOW + timedelta(minutes=10))
        status_10m, body_10m = self.call("POST", "/api/auth/login", json={"username": username, "password": "123456"})
        self.assertEqual(status_10m, 401)
        self.assertTrue("15 phút" in body_10m.get("detail", "").lower() or "khóa" in body_10m.get("detail", "").lower())

        # Bước 4: Hết 15 phút (sau 16 phút), tài khoản tự động mở khóa và đăng nhập thành công
        clock.freeze(NOW + timedelta(minutes=16))
        status_16m, body_16m = self.call("POST", "/api/auth/login", json={"username": username, "password": "123456"})
        self.assertEqual(status_16m, 200, f"Hết 15 phút phải tự động mở khóa cho đăng nhập: {body_16m}")
        self.assertIn("access_token", body_16m)

        # Bước 5: Đặt lại số lần sai: Nhập sai 2 lần rồi đăng nhập đúng -> bộ đếm được reset
        self.call("POST", "/api/auth/login", json={"username": username, "password": "WrongPassword_1"})
        self.call("POST", "/api/auth/login", json={"username": username, "password": "WrongPassword_2"})
        status_reset, _ = self.call("POST", "/api/auth/login", json={"username": username, "password": "123456"})
        self.assertEqual(status_reset, 200, "Đăng nhập đúng phải reset bộ đếm số lần sai")

    def test_18_kiem_thu_s1_02_thu_hoi_token_sau_dang_xuat(self):
        """[S1-02] Kiểm thử yêu cầu đăng xuất: Sau khi đăng xuất, token cũ không được phép gọi API được bảo vệ.
        Nếu token cũ vẫn dùng được gọi API bảo vệ, ghi nhận FAIL (BUG-QA-003).
        Không chấp nhận việc xác nhận kiến trúc stateless là PASS yêu cầu đăng xuất.
        """
        # Bước 1: Đăng nhập lấy access_token hợp lệ
        status_login, body_login = self.call("POST", "/api/auth/login", json={"username": "nhanvien1", "password": "123456"})
        self.assertEqual(status_login, 200, f"Đăng nhập lấy token thất bại: {body_login}")
        token = body_login["access_token"]

        # Kiểm tra token hoạt động bình thường trên API bảo vệ (/api/auth/me) trước khi đăng xuất
        resp_before = self.client.open("/api/auth/me", method="GET", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp_before.status_code, 200, "Token hợp lệ phải truy cập được /api/auth/me")

        # Bước 2: Gọi API đăng xuất (POST /api/auth/logout)
        resp_logout = self.client.open("/api/auth/logout", method="POST", headers={"Authorization": f"Bearer {token}"})
        status_logout = resp_logout.status_code
        body_logout = resp_logout.get_json()

        # Kỳ vọng 1: Endpoint đăng xuất phải tồn tại và xử lý thành công (200 OK hoặc 204 No Content)
        self.assertIn(
            status_logout,
            (200, 204),
            f"S1-02 CHƯA ĐẠT: Endpoint POST /api/auth/logout không tồn tại hoặc lỗi (HTTP {status_logout}). "
            f"Hệ thống Backend chưa hỗ trợ API đăng xuất!"
        )

        # Bước 3: Dùng lại token cũ để gọi API được bảo vệ (/api/auth/me)
        resp_after = self.client.open("/api/auth/me", method="GET", headers={"Authorization": f"Bearer {token}"})
        status_after = resp_after.status_code

        # Kỳ vọng 2: Token cũ phải bị thu hồi phía máy chủ và trả về 401 Unauthorized
        self.assertEqual(
            status_after,
            401,
            f"BUG-QA-003 (S1-02 CHƯA ĐẠT): Sau khi đăng xuất, token cũ vẫn dùng được (HTTP {status_after}) để truy cập API bảo vệ! "
            f"Backend sử dụng stateless serializer mà không có cơ chế thu hồi / blacklist token phía server."
        )


if __name__ == "__main__":
    unittest.main()

