// Layout.jsx — App shell: sidebar + main content
import { apiLogout } from "../api/index.js";

const PAGE_TITLES = {
  dashboard: { title: "Tổng quan",            sub: "Thông tin tài khoản & phân quyền dữ liệu" },
  users:     { title: "Quản lý tài khoản",    sub: "Tạo, tìm kiếm và quản lý người dùng" },
  roles:     { title: "Quản lý vai trò",      sub: "Vai trò, nhóm kinh doanh & quy tắc phân quyền" },
  "change-password": { title: "Đổi mật khẩu", sub: "Cập nhật mật khẩu tài khoản" },
};

function initials(name = "") {
  return name.split(" ").slice(-2).map(p => p[0]).join("").toUpperCase();
}

export default function Layout({ profile, currentPage, onNavigate, onLogout, children }) {
  const { user, menu } = profile;

  async function handleLogout() {
    try { await apiLogout(); } catch (_) { /* ignore */ }
    onLogout();
  }

  const pageInfo = PAGE_TITLES[currentPage] || { title: "CRM", sub: "" };

  return (
    <div className="app-layout">
      {/* ── Sidebar ─────────────────────────── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">💼</div>
          <div className="sidebar-logo-text">
            <strong>CRM System</strong>
            <small>Quản lý Bán hàng</small>
          </div>
        </div>

        {/* User info */}
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials(user.full_name)}</div>
          <div className="sidebar-user-info">
            <strong title={user.full_name}>{user.full_name}</strong>
            <small>{user.role_label}</small>
          </div>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          <div className="sidebar-nav-label">Điều hướng</div>
          {menu.map(item => (
            <button
              key={item.key}
              className={`nav-item${currentPage === item.key ? " active" : ""}`}
              onClick={() => onNavigate(item.key)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <span>🚪</span> Đăng xuất
          </button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────── */}
      <div className="main-content">
        <header className="page-header">
          <div className="page-header-title">
            <h1>{pageInfo.title}</h1>
            {pageInfo.sub && <p>{pageInfo.sub}</p>}
          </div>
          <div className="page-header-actions">
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              background: "var(--gray-50)", border: "1px solid var(--gray-200)",
              borderRadius: 10, padding: "6px 12px", fontSize: ".82rem",
            }}>
              <span style={{ fontSize: "1rem" }}>👤</span>
              <span style={{ color: "var(--gray-600)" }}>{user.email}</span>
            </div>
          </div>
        </header>

        <main className="page-body">
          {children}
        </main>
      </div>
    </div>
  );
}
