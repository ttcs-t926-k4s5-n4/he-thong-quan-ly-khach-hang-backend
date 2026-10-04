from app.users import generate_temporary_password, valid_email


def test_temporary_password_has_letter_and_number() -> None:
    password = generate_temporary_password()
    assert len(password) >= 12
    assert any(character.isalpha() for character in password)
    assert any(character.isdigit() for character in password)


def test_email_validation() -> None:
    assert valid_email("nhanvien@company.vn")
    assert not valid_email("khong-phai-email")
