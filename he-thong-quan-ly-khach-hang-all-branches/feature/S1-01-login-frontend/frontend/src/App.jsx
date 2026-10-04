import { useState } from "react";
import { login } from "./api";
import "./styles.css";

const HOME = {
  admin: ["Trang chủ Quản trị hệ thống", "Quản trị hệ thống"],
  manager: ["Trang chủ Giám đốc kinh doanh", "Giám đốc kinh doanh"],
  employee: ["Trang chủ Nhân viên kinh doanh", "Nhân viên kinh doanh"],
};

function Login({onSuccess}) {
  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const [message,setMessage] = useState("");
  const [loading,setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setMessage("");
    setLoading(true);
    try {
      const result = await login(email.trim(), password);
      window.history.pushState({}, "", result.redirect_url);
      onSuccess(result.user);
    } catch (error) {
      setMessage(error.data?.message || "Email hoặc mật khẩu không đúng.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <div className="brand">CRM</div>
        <p className="eyebrow">S1-01 · ĐĂNG NHẬP HỆ THỐNG</p>
        <h1>Đăng nhập</h1>
        <p className="muted">Đăng nhập bằng email công ty và mật khẩu.</p>
        <form className="form" onSubmit={submit}>
          <label>Email công ty
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)}
              placeholder="nhanvien@company.vn" required />
          </label>
          <label>Mật khẩu
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
          </label>
          {message && <div className="alert">{message}</div>}
          <button disabled={loading}>{loading ? "Đang đăng nhập..." : "Đăng nhập"}</button>
        </form>
        <p className="hint">Sau 5 lần nhập sai liên tiếp, tài khoản bị khóa tạm 15 phút.</p>
      </section>
    </main>
  );
}

function Home({user,onLogout}) {
  const [title,label] = HOME[user.role] || ["Trang chủ", user.role_label || user.role];
  return (
    <main className="page">
      <section className="card center">
        <div className="brand">CRM</div>
        <p className="eyebrow">ĐĂNG NHẬP THÀNH CÔNG</p>
        <h1>{title}</h1>
        <p className="muted">Vai trò: {label}</p>
        <div className="box"><strong>{user.full_name}</strong><span>{user.email}</span></div>
        <button onClick={onLogout}>Quay lại trang đăng nhập</button>
      </section>
    </main>
  );
}

export default function App() {
  const [user,setUser] = useState(null);
  return user
    ? <Home user={user} onLogout={()=>{window.history.pushState({},"","/");setUser(null)}} />
    : <Login onSuccess={setUser} />;
}
