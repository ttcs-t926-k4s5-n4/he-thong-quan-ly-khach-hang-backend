"""SCRUM-89 – Thêm sản phẩm/dịch vụ vào cơ hội để ra giá trị hợp đồng."""
from tests.base import CRMTestCase


class TestScrum89DongSanPham(CRMTestCase):
    def setUp(self):
        super().setUp()
        self.opp = self.make_opp(estimated_value=90_000_000)
        self.url = f"/api/opportunities/{self.opp['id']}/lines"

    def add(self, expect=201, **payload):
        status, body = self.post(self.url, "nhanvien1", payload)
        self.assertEqual(status, expect, body)
        return body

    def test_danh_muc_san_pham_kem_gia_niem_yet(self):
        status, body = self.get("/api/products", "nhanvien1", {"q": "crm"})
        self.assertEqual(status, 200)
        self.assertEqual(body["price_list"]["name"], "Bảng giá niêm yết 2026")
        standard = next(p for p in body["items"] if p["code"] == "CRM-STD")
        self.assertEqual(standard["list_price"], 250_000)
        self.assertEqual(standard["list_price_display"], "250.000 đ/người dùng/tháng")
        self.assertEqual(standard["product_type_label"], "Dịch vụ thuê bao")

    def test_chon_tu_danh_muc_don_gia_mac_dinh_theo_bang_gia(self):
        """Tiêu chí 1: chọn sản phẩm, nhập số lượng, đơn giá mặc định lấy từ bảng giá niêm yết."""
        body = self.add(product_id=self.product("TB-MQ"), quantity=6)
        line = body["line"]
        self.assertEqual((line["unit_price"], line["list_price"], line["line_total"]), (2_500_000, 2_500_000, 15_000_000))
        self.assertFalse(line["price_overridden"])
        self.assertEqual(line["formula"], "6 cái × 2.500.000 đ = 15.000.000 đ")

    def test_nhap_don_gia_rieng_va_chiet_khau(self):
        body = self.add(product_id=self.product("DV-TK"), quantity=1, unit_price=12_000_000, discount_percent=10)
        line = body["line"]
        self.assertEqual(line["line_total"], 10_800_000)
        self.assertTrue(line["price_overridden"])
        self.assertIn("chiết khấu 10%", line["formula"])

    def test_gia_tri_co_hoi_tinh_lai_tu_dong(self):
        """Tiêu chí 2: giá trị cơ hội được tính lại tự động từ các dòng sản phẩm."""
        first = self.add(product_id=self.product("TB-MQ"), quantity=6)
        self.assertEqual(first["opportunity"]["amount"], 15_000_000)
        self.assertEqual(first["opportunity"]["amount_source"], "lines")
        second = self.add(product_id=self.product("DV-DT"), quantity=2.5)
        self.assertEqual(second["opportunity"]["amount"], 22_500_000)
        status, body = self.patch(f"{self.url}/{first['line']['id']}", "nhanvien1", {"quantity": 10})
        self.assertEqual(status, 200, body)
        self.assertEqual(body["opportunity"]["amount"], 32_500_000)
        status, body = self.delete(f"{self.url}/{second['line']['id']}", "nhanvien1")
        self.assertEqual(body["opportunity"]["amount"], 25_000_000)
        status, body = self.delete(f"{self.url}/{first['line']['id']}", "nhanvien1")
        self.assertEqual((body["opportunity"]["amount"], body["opportunity"]["amount_source"]), (90_000_000, "manual"))
        self.assertIn("quay về giá trị dự kiến", body["message"])
        opp = self.get(f"/api/opportunities/{self.opp['id']}", "nhanvien1")[1]
        self.assertEqual(opp["amount"], 90_000_000)

    def test_thue_bao_khai_bao_so_ky_va_gia_tri_theo_nam(self):
        """Tiêu chí 3: dịch vụ thuê bao khai báo số kỳ và giá trị hợp đồng theo năm."""
        body = self.add(product_id=self.product("CRM-PRO"), quantity=50, periods=30, discount_percent=5)
        line = body["line"]
        self.assertEqual(line["line_total"], 641_250_000)        # 50 × 450.000 × 0,95 × 30 tháng
        self.assertEqual(line["annual_value"], 256_500_000)      # quy đổi 12 tháng
        self.assertEqual(line["term_months"], 30)
        self.assertEqual([(y["contract_year"], y["periods"], y["value"]) for y in line["yearly_breakdown"]],
                         [(1, 12, 256_500_000), (2, 12, 256_500_000), (3, 6, 128_250_000)])
        self.assertEqual(sum(y["value"] for y in line["yearly_breakdown"]), line["line_total"])
        self.assertEqual(body["opportunity"]["recurring_annual_value"], 256_500_000)
        status, lines = self.get(self.url, "nhanvien1")
        self.assertEqual(lines["totals"]["subscription_total"], 641_250_000)

    def test_thue_bao_theo_quy_va_theo_nam(self):
        quarterly = self.add(product_id=self.product("HT-QUY"), quantity=1, periods=8)["line"]
        self.assertEqual((quarterly["line_total"], quarterly["annual_value"], quarterly["term_months"]),
                         (48_000_000, 24_000_000, 24))
        yearly = self.add(product_id=self.product("MC-NAM"), quantity=1, periods=2)["line"]
        self.assertEqual((yearly["line_total"], yearly["annual_value"]), (48_000_000, 24_000_000))

    def test_quy_tac_so_ky(self):
        body = self.add(expect=422, product_id=self.product("CRM-STD"), quantity=5)
        self.assertFieldError(body, "periods", "khai báo số kỳ")
        body = self.add(expect=422, product_id=self.product("TB-MQ"), quantity=1, periods=3)
        self.assertFieldError(body, "periods", "Chỉ dịch vụ thuê bao")

    def test_san_pham_chua_co_gia_niem_yet_phai_nhap_don_gia(self):
        body = self.add(expect=422, product_id=self.product("DV-TUYCHINH"), quantity=10)
        self.assertFieldError(body, "unit_price", "chưa có trong bảng giá niêm yết")
        line = self.add(product_id=self.product("DV-TUYCHINH"), quantity=10, unit_price=800_000)["line"]
        self.assertEqual((line["list_price"], line["line_total"]), (None, 8_000_000))

    def test_quay_ve_gia_niem_yet(self):
        line = self.add(product_id=self.product("TB-MIN"), quantity=2, unit_price=1_500_000)["line"]
        status, body = self.patch(f"{self.url}/{line['id']}", "nhanvien1", {"unit_price": None})
        self.assertEqual(status, 200)
        self.assertEqual((body["line"]["unit_price"], body["line"]["line_total"]), (1_800_000, 3_600_000))

    def test_du_lieu_dong_khong_hop_le(self):
        body = self.add(expect=422, product_id=self.product("TB-MQ"), quantity=0, discount_percent=120)
        self.assertFieldError(body, "quantity", "phải lớn hơn 0")
        self.assertFieldError(body, "discount_percent", "không được lớn hơn 100")
        body = self.add(expect=422, product_id=99999, quantity=1)
        self.assertFieldError(body, "product_id", "không có trong danh mục")
        line = self.add(product_id=self.product("TB-MQ"), quantity=1)["line"]
        status, body = self.patch(f"{self.url}/{line['id']}", "nhanvien1", {"product_id": self.product("TB-MIN")})
        self.assertEqual(status, 422)
        self.assertIn("xoá dòng này", body["detail"])

    def test_khong_nhap_tay_gia_tri_khi_da_co_dong_san_pham(self):
        self.add(product_id=self.product("TB-MQ"), quantity=1)
        status, body = self.patch(f"/api/opportunities/{self.opp['id']}", "nhanvien1", {"estimated_value": 1})
        self.assertEqual(status, 409)
        self.assertIn("tính tự động", body["detail"])

    def test_co_hoi_da_dong_khong_sua_dong_san_pham(self):
        self.assertEqual(self.move(self.opp["id"], "lost")[0], 200)
        body = self.add(expect=409, product_id=self.product("TB-MQ"), quantity=1)
        self.assertIn("đã đóng", body["detail"])

    def test_nguoi_khac_khong_them_duoc_vao_co_hoi_cua_minh(self):
        status, _ = self.post(self.url, "nhanvien2", {"product_id": self.product("TB-MQ"), "quantity": 1})
        self.assertEqual(status, 404)
        status, _ = self.post(self.url, "truongnhom1", {"product_id": self.product("TB-MQ"), "quantity": 1})
        self.assertEqual(status, 201)
