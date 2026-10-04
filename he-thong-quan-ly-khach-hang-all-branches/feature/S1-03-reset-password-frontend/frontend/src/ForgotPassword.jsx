import { useState } from "react";
import { requestPasswordReset } from "./api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!email.trim()) {
      setError("Vui lòng nhập email.");
      return;
    }

    setLoading(true);
    try {
      const result = await requestPasswordReset(email.trim());
      setMessage(result.message);
    } catch (requestError) {
      setError(
        requestError.data?.errors?.email ||
          requestError.data?.message ||
          "Không thể gửi yêu cầu đặt lại mật khẩu."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card" aria-labelledby="page-title">
      <div className="card-heading">
        <p className="eyebrow">S1-03 · Khôi phục tài khoản</p>
        <h1 id="page-title">Quên mật khẩu?</h1>
        <p className="muted">
          Nhập email công ty. Nếu email đã được đăng ký, hệ thống sẽ gửi một
          liên kết đặt lại mật khẩu có hiệu lực trong 30 phút.
        </p>
      </div>

      {message ? (
        <div className="status success" role="status">
          <strong>Đã xử lý yêu cầu</strong>
          <span>{message}</span>
        </div>
      ) : (
        <form className="form" onSubmit={handleSubmit} noValidate>
          <label>
            Email công ty
            <input
              type="email"
              autoComplete="email"
              placeholder="ten@congty.vn"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <p className="hint">
            Vì lý do bảo mật, hệ thống không cho biết email có tồn tại hay không.
          </p>

          {error && <div className="status error">{error}</div>}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Đang gửi..." : "Gửi liên kết đặt lại"}
          </button>
        </form>
      )}
    </section>
  );
}
