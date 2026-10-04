from app.account import new_password_error


def test_password_too_short() -> None:
    assert "ít nhất 8 ký tự" in str(new_password_error("Ab1"))


def test_password_requires_number() -> None:
    assert "một chữ số" in str(new_password_error("Abcdefgh"))


def test_password_requires_letter() -> None:
    assert "một chữ cái" in str(new_password_error("12345678"))


def test_valid_password() -> None:
    assert new_password_error("NewSecure123") is None
