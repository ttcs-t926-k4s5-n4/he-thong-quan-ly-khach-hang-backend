// ResetPasswordPage.jsx — S1-03 (đặt lại mật khẩu qua link email)
import { useEffect, useState } from "react";
import { apiCheckResetToken, apiDoResetPassword } from "../api/index.js";

function strengthOf(pwd) {
  if (!pwd) return { level: 0, label: "", color: "#e5e7eb" };
  let score = 0;
  if (pwd.length >= 8)  score++;
  if (pwd.length >= 12) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^a-zA-Z0-9]/.test(pwd)) score++;
  if (score <= 1) return { level: 20,  label: "Rất yếu",   color: "#ef4444" };
  if (score === 2) return { level: 40,  label: "Yếu",       color: "#f59e0b" };
  if (score === 3) return { level: 60,  label: "Trung bình", color: "#eab308" };
  if (score === 4) return { level: 80,  label: "Mạnh",       color: "#10b981" };
  return                  { level: 100, label: "Rất mạnh",   color: "#059669" };
}

export default function ResetPasswordPage({ token, onSuccess }) {
  const [checking, setChecking] = useState(true);
  const [valid, setValid]       = useState(false);
  const [newPwd, setNewPwd]     = useState("");
  const [confirm, setConfirm]   = useState("");
  const [errors, setErrors]     = useState({});
  const [loading, setLoading]   = useState(false);
  const [done, setDone]         = useState(false);

  useEffect(() => {
    apiCheckResetToken(token)
      .then(() => setValid(true))
      .catch(() => setValid(false))
      .finally(() => setChecking(false));
  }, [token]);

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors({});
    setLoading(true);
    try {
      await apiDoResetPassword(token, {
        new_password: newPwd,
        new_password_confirmation: confirm,
      });
      setDone(true);
    } catch (err) {
      if (err.data?.errors) setErrors(err.data.errors);
      else setErrors({ _: err.data?.message || "Đặt lại mật khẩu thất bại." });
    } finally {
      setLoading(false);
    }
  }

  const strength = strengthOf(newPwd);

  if (checking) return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "var(--indigo-900)" }}>
      <div style={{ color: "white", textAlign: "center" }}>
        <div className="spinner" style={{ margin: "0 auto 12px", width: 32, height: 32, borderWidth: 3 }} />
        <p>Đang kiểm tra liên kết...</p>
      </div>
    </div>
  );

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-logo">🔒</div>
        <h1>Đặt lại mật khẩu</h1>
        <p>Tạo mật khẩu mới mạnh hơn để bảo vệ tài khoản của bạn.</p>
        <div className="auth-brand-features">
          <div className="auth-brand-feature"><span>✅</span><span>Tối thiểu 8 ký tự</span></div>
          <div className="auth-brand-feature"><span>🔤</span><span>Có ít nhất 1 chữ cái</span></div>
          <div className="auth-brand-feature"><span>🔢</span><span>Có ít nhất 1 chữ số</span></div>
        </div>
      </div>

      <div className="auth-card-wrap">
        <div className="auth-card">
          <div className="auth-eyebrow">🔒 S1-03 · ĐẶT LẠI MẬT KHẨU</div>

          {!valid ? (
            <>
              <h2>Liên kết không hợp lệ</h2>
              <div className="alert alert-error" style={{ marginTop: 16 }}>
                <span>⚠️</span>
                <span>Liên kết đặt lại mật khẩu đã hết hạn hoặc đã được sử dụng. Vui lòng yêu cầu liên kết mới.</span>
              </div>
              <button className="btn btn-primary" onClick={onSuccess} style={{ marginTop: 8 }}>
                Quay lại đăng nhập
              </button>
            </>
          ) : done ? (
            <>
              <h2>Mật khẩu đã được đặt lại!</h2>
              <div className="alert alert-success" style={{ marginTop: 16 }}>
                <span>✅</span>
                <span>Mật khẩu mới đã được lưu thành công. Vui lòng đăng nhập với mật khẩu mới.</span>
              </div>
              <button className="btn btn-primary" onClick={onSuccess} style={{ marginTop: 8 }}>
                Đăng nhập ngay
              </button>
            </>
          ) : (
            <>
              <h2>Tạo mật khẩu mới</h2>
              <p className="auth-sub">Nhập và xác nhận mật khẩu mới của bạn.</p>

              {errors._ && <div className="alert alert-error"><span>⚠️</span><span>{errors._}</span></div>}

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="new-pwd">Mật khẩu mới</label>
                  <input
                    id="new-pwd"
                    className={`form-input${errors.new_password ? " error" : ""}`}
                    type="password"
                    value={newPwd}
                    onChange={e => setNewPwd(e.target.value)}
                    placeholder="Tối thiểu 8 ký tự, gồm chữ và số"
                    required
                  />
                  {newPwd && (
                    <div style={{ marginTop: 6 }}>
                      <div className="pwd-strength">
                        <div className="pwd-strength-bar" style={{ width: `${strength.level}%`, background: strength.color }} />
                      </div>
                      <small style={{ color: strength.color, fontSize: ".78rem" }}>{strength.label}</small>
                    </div>
                  )}
                  {errors.new_password && <div className="field-error">{errors.new_password}</div>}
                </div>

                <div className="form-group">
                  <label htmlFor="confirm-pwd">Xác nhận mật khẩu</label>
                  <input
                    id="confirm-pwd"
                    className={`form-input${errors.new_password_confirmation ? " error" : ""}`}
                    type="password"
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    placeholder="Nhập lại mật khẩu mới"
                    required
                  />
                  {errors.new_password_confirmation && <div className="field-error">{errors.new_password_confirmation}</div>}
                </div>

                <button className="btn btn-primary" type="submit" disabled={loading}>
                  {loading ? <><span className="spinner" /> Đang lưu...</> : "Đặt lại mật khẩu"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
