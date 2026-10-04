import ForgotPassword from "./ForgotPassword";
import ResetPassword from "./ResetPassword";
import "./styles.css";

function resolvePage() {
  const path = window.location.pathname;

  if (path === "/" || path === "/forgot-password") {
    return { type: "forgot" };
  }

  const resetMatch = path.match(/^\/reset-password\/([^/]+)$/);
  if (resetMatch) {
    return {
      type: "reset",
      token: decodeURIComponent(resetMatch[1]),
    };
  }

  return { type: "not-found" };
}

export default function App() {
  const page = resolvePage();

  return (
    <main className="page">
      <div className="shell">
        <header className="topbar">
          <div>
            <span className="brand">CRM</span>
            <span className="separator">/</span>
            <span>Hệ thống quản lý khách hàng</span>
          </div>
          <span className="secure-label">Khôi phục tài khoản</span>
        </header>

        {page.type === "forgot" && <ForgotPassword />}

        {page.type === "reset" && <ResetPassword token={page.token} />}

        {page.type === "not-found" && (
          <section className="card result-card">
            <h1>Không tìm thấy trang</h1>
            <a className="primary-button link-button" href="/forgot-password">
              Về trang quên mật khẩu
            </a>
          </section>
        )}
      </div>
    </main>
  );
}
