import { useEffect, useState } from "react";
import { inspectResetToken, resetPassword } from "./api";

function passwordRuleError(password) {
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

export default function ResetPassword({ token }) {
  const [checking, setChecking] = useState(true);
  const [validLink, setValidLink] = useState(false);
  const [linkMessage, setLinkMessage] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    inspectResetToken(token)
      .then(() => {
        setValidLink(true);
        setLinkMessage("");
      })
      .catch((error) => {
        setValidLink(false);
        setLinkMessage(
          error.data?.message || "Liên kết không hợp lệ hoặc đã hết hạn."
        );
      })
      .finally(() => setChecking(false));
  }, [token]);

  async function handleSubmit(event) {
    event.preventDefault();
    setErrors({});
    setSuccess("");

    const nextErrors = {};
    const passwordError = passwordRuleError(password);

    if (passwordError) {
      nextErrors.password = passwordError;
    }

    if (!confirmation) {
      nextErrors.password_confirmation = "Vui lòng xác nhận mật khẩu mới.";
    } else if (password !== confirmation) {
      nextErrors.password_confirmation = "Mật khẩu xác nhận không khớp.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setLoading(true);
    try {
      const result = await resetPassword(token, password, confirmation);
      setSuccess(result.message || "Đặt lại mật khẩu thành công.");
      setValidLink(false);
      setPassword("");
      setConfirmation("");
    } catch (error) {
      if (error.data?.errors) {
        setErrors(error.data.errors);
      } else {
        setValidLink(false);
        setLinkMessage(
          error.data?.message || "Liên kết không hợp lệ hoặc đã hết hạn."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  if (checking) {
    return <section className="card">Đang kiểm tra liên kết...</section>;
  }

  if (success) {
    return (
      <section className="card result-card">
        <p className="eyebrow">Hoàn tất</p>
        <h1>Đặt lại mật khẩu thành công</h1>
        <p className="muted">{success}</p>
        <p className="hint">
          Liên kết này đã được sử dụng và không thể dùng lại.
        </p>
        <a className="primary-button link-button" href="/forgot-password">
          Hoàn tất
        </a>
      </section>
    );
  }

  if (!validLink) {
    return (
      <section className="card result-card">
        <p className="eyebrow">Không thể sử dụng</p>
        <h1>Liên kết không hợp lệ</h1>
        <p className="muted">{linkMessage}</p>
        <a className="primary-button link-button" href="/forgot-password">
          Yêu cầu liên kết mới
        </a>
      </section>
    );
  }

  return (
    <section className="card" aria-labelledby="page-title">
      <div className="card-heading">
        <p className="eyebrow">S1-03 · Bảo mật tài khoản</p>
        <h1 id="page-title">Đặt mật khẩu mới</h1>
        <p className="muted">
          Liên kết đặt lại chỉ dùng được một lần và có hiệu lực trong 30 phút.
        </p>
      </div>

      <form className="form" onSubmit={handleSubmit} noValidate>
        <label>
          Mật khẩu mới
          <input
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {errors.password && (
            <small className="field-error">{errors.password}</small>
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
          {errors.password_confirmation && (
            <small className="field-error">
              {errors.password_confirmation}
            </small>
          )}
        </label>

        <p className="hint">
          Mật khẩu mới tối thiểu 8 ký tự, có ít nhất một chữ cái và một chữ số.
        </p>

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Đang cập nhật..." : "Đặt lại mật khẩu"}
        </button>
      </form>
    </section>
  );
}
