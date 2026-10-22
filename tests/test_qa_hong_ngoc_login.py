"""QA bổ sung: từ chối đăng nhập khi thiếu trường bắt buộc."""
from tests.base import CRMTestCase


class TestQAHongNgocLoginValidation(CRMTestCase):
    def assert_login_rejected(self, payload, expected_fields):
        # Gửi dữ liệu đăng nhập không đầy đủ.
        status, body = self.call(
            "POST", "/api/auth/login", json=payload
        )

        # Phải báo lỗi dữ liệu và không cấp token.
        self.assertEqual(status, 422, body)
        self.assertNotIn("access_token", body)
        self.assertNotIn("user", body)

        # Kiểm tra chính xác các trường bị thiếu.
        errors = body.get("errors", [])
        self.assertEqual(
            {error["field"] for error in errors},
            set(expected_fields),
            body,
        )

        for field, label in expected_fields.items():
            self.assertFieldError(
                body, field, f"{label} là bắt buộc."
            )

    def test_thieu_ten_dang_nhap(self):
        self.assert_login_rejected(
            {"password": "123456"},
            {"username": "Tên đăng nhập"},
        )

    def test_thieu_mat_khau(self):
        self.assert_login_rejected(
            {"username": "nhanvien1"},
            {"password": "Mật khẩu"},
        )

    def test_json_rong_thieu_ca_hai_truong(self):
        self.assert_login_rejected(
            {},
            {
                "username": "Tên đăng nhập",
                "password": "Mật khẩu",
            },
        )
