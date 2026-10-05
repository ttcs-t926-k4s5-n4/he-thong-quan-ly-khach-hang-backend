// ForgotPasswordPage.jsx — S1-03 (quên mật khẩu)
import { useState } from "react";
import { apiForgotPassword } from "../api/index.js";

export default function ForgotPasswordPage({ onBack }) {
  const [email, setEmail]     = useState("");
  const [message, setMessage] = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent]       = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setMessage("");
    setLoading(true);
    try {
      const res = await apiForgotPassword(email.trim());
      setMessage(res.message);
      setSent(true);
    } catch (err) {
      setError(err.data?.message || "Đã xảy ra lỗi. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-logo">📧</div>
        <h1>Quên mật khẩu</h1>
        <p>Nhập email công ty của bạn, chúng tôi sẽ gửi liên kết đặt lại mật khẩu.</p>
        <div className="auth-brand-features">
          <div className="auth-brand-feature"><span>🔗</span><span>Link có hiệu lực 30 phút</span></div>
          <div className="auth-brand-feature"><span>🔒</span><span>Chỉ dùng được một lần</span></div>
          <div className="auth-brand-feature"><span>🛡️</span><span>Không tiết lộ email có tồn tại</span></div>
        </div>
      </div>

      <div className="auth-card-wrap">
        <div className="auth-card">
          <div className="auth-eyebrow">📧 S1-03 · QUÊN MẬT KHẨU</div>
          <h2>Đặt lại mật khẩu</h2>
          <p className="auth-sub">Nhập email công ty của bạn để nhận liên kết đặt lại.</p>

          {error   && <div className="alert alert-error"  ><span>⚠️</span><span>{error}</span></div>}
          {message && <div className="alert alert-success"><span>✅</span><span>{message}</span></div>}

          {!sent ? (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="forgot-email">Email công ty</label>
                <input
                  id="forgot-email"
                  className="form-input"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="nhanvien@company.vn"
                  required
                />
              </div>
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? <><span className="spinner" /> Đang gửi...</> : "Gửi liên kết đặt lại"}
              </button>
            </form>
          ) : (
            <div style={{ textAlign: "center", paddingTop: 8 }}>
              <div style={{ fontSize: "3rem", marginBottom: 12 }}>📬</div>
              <p style={{ color: "var(--gray-600)", fontSize: ".9rem", lineHeight: 1.7 }}>
                Kiểm tra hộp thư của bạn và nhấn vào liên kết trong email.<br />
                Liên kết có hiệu lực <strong>30 phút</strong>.
              </p>
              <button className="btn btn-ghost" onClick={() => { setSent(false); setMessage(""); }} style={{ marginTop: 12 }}>
                Gửi lại email
              </button>
            </div>
          )}

          <p className="auth-hint">
            <button className="auth-link" onClick={onBack} type="button">← Quay lại đăng nhập</button>
          </p>
        </div>
      </div>
    </div>
  );
}
