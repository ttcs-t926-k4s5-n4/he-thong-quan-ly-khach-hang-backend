import { useState } from "react";
import { login } from "./api";

export default function LoginForm({ onLoggedIn }) {
  const [email, setEmail] = useState("demo@company.local");
  const [password, setPassword] = useState("Demo@123456");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    try {
      const result = await login(email.trim(), password);
      onLoggedIn(result.user);
    } catch (error) {
      setMessage(error.data?.message || "Đăng nhập thất bại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="card-heading">
        <p className="eyebrow">CRM</p>
        <h1>Đăng nhập</h1>
        <p className="muted">
          Đăng nhập để kiểm thử chức năng S1-04 đổi mật khẩu.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <label>
          Email công ty
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label>
          Mật khẩu
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {message && <div className="alert error">{message}</div>}

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>
      </form>
    </section>
  );
}
