import { useState } from "react";
import { changePassword } from "./api";
import { validateNewPassword } from "./validation";

export default function ChangePasswordForm({ user }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function validate() {
    const nextErrors = {};

    if (!currentPassword) {
      nextErrors.current_password = "Vui lòng nhập mật khẩu hiện tại.";
    }

    const passwordError = validateNewPassword(newPassword);
    if (passwordError) {
      nextErrors.new_password = passwordError;
    }

    if (!confirmation) {
      nextErrors.new_password_confirmation =
        "Vui lòng xác nhận mật khẩu mới.";
    } else if (newPassword !== confirmation) {
      nextErrors.new_password_confirmation =
        "Mật khẩu xác nhận không khớp.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSuccessMessage("");

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      const result = await changePassword({
        currentPassword,
        newPassword,
        confirmation,
      });

      setErrors({});
      setSuccessMessage(
        `${result.message} Các phiên đăng nhập khác đã được thu hồi.`
      );
      setCurrentPassword("");
      setNewPassword("");
      setConfirmation("");
    } catch (error) {
      if (error.status === 401) {
        setErrors({
          form:
            error.data?.message ||
            "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
        });
      } else {
        setErrors({
          ...(error.data?.errors || {}),
          form: error.data?.message || "Không thể đổi mật khẩu.",
        });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="card-heading">
        <p className="eyebrow">S1-04</p>
        <h1>Đổi mật khẩu</h1>
        <p className="muted">
          Tài khoản: <strong>{user.email}</strong>
        </p>
      </div>

      <div className="requirements">
        <span>Yêu cầu mật khẩu mới</span>
        <ul>
          <li>Tối thiểu 8 ký tự</li>
          <li>Có ít nhất 1 chữ cái</li>
          <li>Có ít nhất 1 chữ số</li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <label>
          Mật khẩu hiện tại
          <input
            type="password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
          {errors.current_password && (
            <small className="field-error">{errors.current_password}</small>
          )}
        </label>

        <label>
          Mật khẩu mới
          <input
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
          {errors.new_password && (
            <small className="field-error">{errors.new_password}</small>
          )}
        </label>

        <label>
          Xác nhận mật khẩu mới
          <input
            type="password"
            autoComplete="new-password"
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
          />
          {errors.new_password_confirmation && (
            <small className="field-error">
              {errors.new_password_confirmation}
            </small>
          )}
        </label>

        {errors.form && <div className="alert error">{errors.form}</div>}
        {successMessage && (
          <div className="alert success">{successMessage}</div>
        )}

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Đang cập nhật..." : "Đổi mật khẩu"}
        </button>
      </form>
    </section>
  );
}
