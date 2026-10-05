// ChangePasswordPage.jsx — S1-04
import { useState } from "react";
import { apiChangePassword } from "../api/index.js";

function strengthOf(pwd) {
  if (!pwd) return { level: 0, color: "#e5e7eb", label: "" };
  let s = 0;
  if (pwd.length >= 8) s++;
  if (pwd.length >= 12) s++;
  if (/[A-Z]/.test(pwd)) s++;
  if (/[0-9]/.test(pwd)) s++;
  if (/[^a-zA-Z0-9]/.test(pwd)) s++;
  const levels = [
    { level: 0,   color: "#e5e7eb", label: "" },
    { level: 20,  color: "#ef4444", label: "Rất yếu" },
    { level: 40,  color: "#f59e0b", label: "Yếu" },
    { level: 60,  color: "#eab308", label: "Trung bình" },
    { level: 80,  color: "#10b981", label: "Mạnh" },
    { level: 100, color: "#059669", label: "Rất mạnh" },
  ];
  return levels[Math.min(s, 5)];
}

export default function ChangePasswordPage({ onSessionExpired }) {
  const [form, setForm] = useState({ current: "", newPwd: "", confirm: "" });
  const [errors, setErrors]   = useState({});
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showFields, setShowFields] = useState({ current: false, new: false, confirm: false });

  function set(key, val) { setForm(f => ({ ...f, [key]: val })); setErrors(e => ({ ...e, [key]: undefined })); }
  function toggleShow(key) { setShowFields(f => ({ ...f, [key]: !f[key] })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors({}); setSuccess(false);
    setLoading(true);
    try {
      await apiChangePassword({
        current_password: form.current,
        new_password: form.newPwd,
        new_password_confirmation: form.confirm,
      });
      setSuccess(true);
      setForm({ current: "", newPwd: "", confirm: "" });
    } catch (err) {
      if (err.status === 401) { onSessionExpired?.(); return; }
      setErrors(err.data?.errors || { _: err.data?.message || "Đổi mật khẩu thất bại." });
    } finally {
      setLoading(false);
    }
  }

  const strength = strengthOf(form.newPwd);

  return (
    <div className="change-pwd-page">
      <div className="card">
        <div className="card-header">
          <div>
            <h3>🔒 Đổi mật khẩu</h3>
            <p style={{ fontSize: ".82rem", color: "var(--gray-500)", marginTop: 2 }}>S1-04 · Cập nhật mật khẩu tài khoản của bạn</p>
          </div>
        </div>
        <div className="card-body">
          {success && (
            <div className="alert alert-success">
              <span>✅</span>
              <span>Mật khẩu đã được cập nhật thành công! Các phiên đăng nhập khác đã bị thu hồi.</span>
            </div>
          )}
          {errors._ && <div className="alert alert-error"><span>⚠️</span><span>{errors._}</span></div>}

          <form onSubmit={handleSubmit}>
            {/* Current password */}
            <div className="form-group">
              <label htmlFor="cur-pwd">Mật khẩu hiện tại</label>
              <div style={{ position: "relative" }}>
                <input
                  id="cur-pwd"
                  className={`form-input${errors.current_password ? " error" : ""}`}
                  type={showFields.current ? "text" : "password"}
                  value={form.current}
                  onChange={e => set("current", e.target.value)}
                  placeholder="Nhập mật khẩu hiện tại"
                  required
                  style={{ paddingRight: 42 }}
                />
                <button type="button" onClick={() => toggleShow("current")} style={eyeStyle}>{showFields.current ? "🙈" : "👁️"}</button>
              </div>
              {errors.current_password && <div className="field-error">{errors.current_password}</div>}
            </div>

            {/* New password */}
            <div className="form-group">
              <label htmlFor="new-pwd-c">Mật khẩu mới</label>
              <div style={{ position: "relative" }}>
                <input
                  id="new-pwd-c"
                  className={`form-input${errors.new_password ? " error" : ""}`}
                  type={showFields.new ? "text" : "password"}
                  value={form.newPwd}
                  onChange={e => set("newPwd", e.target.value)}
                  placeholder="Tối thiểu 8 ký tự, gồm chữ và số"
                  required
                  style={{ paddingRight: 42 }}
                />
                <button type="button" onClick={() => toggleShow("new")} style={eyeStyle}>{showFields.new ? "🙈" : "👁️"}</button>
              </div>
              {form.newPwd && (
                <div style={{ marginTop: 6 }}>
                  <div className="pwd-strength">
                    <div className="pwd-strength-bar" style={{ width: `${strength.level}%`, background: strength.color }} />
                  </div>
                  <small style={{ color: strength.color, fontSize: ".78rem" }}>{strength.label}</small>
                </div>
              )}
              <p className="pwd-hint">Tối thiểu 8 ký tự, phải có ít nhất 1 chữ cái và 1 chữ số.</p>
              {errors.new_password && <div className="field-error">{errors.new_password}</div>}
            </div>

            {/* Confirm */}
            <div className="form-group">
              <label htmlFor="confirm-pwd-c">Xác nhận mật khẩu mới</label>
              <div style={{ position: "relative" }}>
                <input
                  id="confirm-pwd-c"
                  className={`form-input${errors.new_password_confirmation ? " error" : ""}`}
                  type={showFields.confirm ? "text" : "password"}
                  value={form.confirm}
                  onChange={e => set("confirm", e.target.value)}
                  placeholder="Nhập lại mật khẩu mới"
                  required
                  style={{ paddingRight: 42 }}
                />
                <button type="button" onClick={() => toggleShow("confirm")} style={eyeStyle}>{showFields.confirm ? "🙈" : "👁️"}</button>
              </div>
              {errors.new_password_confirmation && <div className="field-error">{errors.new_password_confirmation}</div>}
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
              <button className="btn btn-primary" type="submit" disabled={loading} style={{ flex: 1 }}>
                {loading ? <><span className="spinner" /> Đang lưu...</> : "Cập nhật mật khẩu"}
              </button>
            </div>
          </form>

          <div className="alert alert-info" style={{ marginTop: 20 }}>
            <span>ℹ️</span>
            <span>Sau khi đổi mật khẩu, tất cả các phiên đăng nhập trên thiết bị khác sẽ bị thu hồi.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

const eyeStyle = {
  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
  background: "none", border: "none", cursor: "pointer", fontSize: "1.1rem", opacity: .6,
};
