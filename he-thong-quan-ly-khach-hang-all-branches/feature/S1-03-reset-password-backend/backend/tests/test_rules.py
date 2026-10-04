from app.password_reset import (
    GENERIC_RESET_MESSAGE,
    is_valid_email,
    password_rule_error,
)


def test_generic_message_does_not_reveal_account_existence() -> None:
    assert "email đã được đăng ký" in GENERIC_RESET_MESSAGE
    assert "không tồn tại" not in GENERIC_RESET_MESSAGE


def test_email_validation() -> None:
    assert is_valid_email("user@company.vn")
    assert not is_valid_email("khong-phai-email")


def test_password_policy() -> None:
    assert password_rule_error("Ab1") is not None
    assert password_rule_error("abcdefgh") is not None
    assert password_rule_error("12345678") is not None
    assert password_rule_error("Secure123") is None
