// LoginPage.jsx — S1-01 (đăng nhập) + S1-02 (session) + S1-10 (lock)
import { useState } from "react";
import { apiLogin } from "../api/index.js";

export default function LoginPage({ onSuccess, onForgot }) {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [showPwd, setShowPwd]   = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await apiLogin(email.trim(), password);
      onSuccess(result.user, result.redirect_url);
    } catch (err) {
      setError(err.data?.message || "Email hoặc mật khẩu không đúng.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      {/* Brand panel */}
      <div className="auth-brand">
        <div className="auth-brand-logo">💼</div>
        <h1>CRM System</h1>
        <p>Hệ thống Quản lý Bán hàng — Tích hợp đầy đủ Sprint 1</p>
        <div className="auth-brand-features">
          <div className="auth-brand-feature"><span>🔐</span><span>Đăng nhập bảo mật với chống brute-force</span></div>
          <div className="auth-brand-feature"><span>🔑</span><span>Phân quyền dữ liệu theo vai trò</span></div>
          <div className="auth-brand-feature"><span>👥</span><span>Quản lý tài khoản & vai trò nhóm</span></div>
          <div className="auth-brand-feature"><span>📧</span><span>Reset mật khẩu qua email an toàn</span></div>
        </div>
      </div>

      {/* Form panel */}
      <div className="auth-card-wrap">
        <div className="auth-card">
          <div className="auth-eyebrow">🔐 S1-01 · ĐĂNG NHẬP HỆ THỐNG</div>
          <h2>Chào mừng trở lại</h2>
          <p className="auth-sub">Đăng nhập bằng email công ty và mật khẩu của bạn.</p>

          {error && (
            <div className="alert alert-error">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email công ty</label>
              <input
                id="email"
                className="form-input"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="nhanvien@company.vn"
                autoComplete="email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Mật khẩu</label>
              <div style={{ position: "relative" }}>
                <input
                  id="password"
                  className="form-input"
                  type={showPwd ? "text" : "password"}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu"
                  autoComplete="current-password"
                  required
                  style={{ paddingRight: 42 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  style={{
                    position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                    background: "none", border: "none", cursor: "pointer", fontSize: "1.1rem", opacity: .6
                  }}
                  title={showPwd ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showPwd ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button className="btn btn-primary" type="submit" disabled={loading} style={{ marginTop: 4 }}>
              {loading ? <><span className="spinner" /> Đang đăng nhập...</> : "Đăng nhập"}
            </button>
          </form>

          <p className="auth-hint">
            Quên mật khẩu?{" "}
            <button className="auth-link" onClick={onForgot} type="button">
              Đặt lại ngay
            </button>
          </p>
          <p className="auth-hint" style={{ fontSize: ".78rem", marginTop: 8 }}>
            Sau 5 lần nhập sai liên tiếp, tài khoản sẽ bị khóa tạm 15 phút.
          </p>
        </div>
      </div>
    </div>
  );
}
