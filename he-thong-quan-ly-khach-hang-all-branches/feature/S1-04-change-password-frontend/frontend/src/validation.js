export function validateNewPassword(password) {
  if (password.length < 8) {
    return "Mật khẩu mới phải có ít nhất 8 ký tự.";
  }

  if (!/[A-Za-z]/.test(password)) {
    return "Mật khẩu mới phải có ít nhất một chữ cái.";
  }

  if (!/[0-9]/.test(password)) {
    return "Mật khẩu mới phải có ít nhất một chữ số.";
  }

  return "";
}
