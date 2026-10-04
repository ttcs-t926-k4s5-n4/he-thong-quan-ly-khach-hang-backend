// DashboardPage.jsx — S1-05 (phân quyền dữ liệu) + S1-06 (menu theo vai trò) + S1-07 (thông báo lỗi)
export default function DashboardPage({ profile }) {
  const { user, scope, menu } = profile;

  const roleConfig = {
    admin: {
      gradient: "linear-gradient(135deg,#4338ca 0%,#7c3aed 100%)",
      emoji: "🛡️",
      desc: "Bạn có quyền truy cập toàn bộ hệ thống. Quản lý tài khoản, vai trò và dữ liệu của tất cả nhân viên.",
    },
    manager: {
      gradient: "linear-gradient(135deg,#0369a1 0%,#0891b2 100%)",
      emoji: "📊",
      desc: "Bạn có thể xem dữ liệu của nhóm và toàn công ty. Có thể xuất báo cáo Excel.",
    },
    employee: {
      gradient: "linear-gradient(135deg,#047857 0%,#059669 100%)",
      emoji: "👤",
      desc: "Bạn có thể xem và quản lý dữ liệu khách hàng của chính mình.",
    },
  };
  const cfg = roleConfig[user.role] || roleConfig.employee;

  const scopeItems = [
    { label: "Xem tất cả dữ liệu",      allowed: !!scope.can_view_all_data,   icon: "📋" },
    { label: "Xem dữ liệu nhóm",         allowed: !!scope.can_view_team,       icon: "👥" },
    { label: "Xem dữ liệu của mình",     allowed: !!scope.can_view_own_data || !!scope.can_view_all_data, icon: "👤" },
    { label: "Quản lý tài khoản người dùng", allowed: !!scope.can_manage_users, icon: "⚙️" },
    { label: "Quản lý vai trò & nhóm",   allowed: !!scope.can_manage_roles,    icon: "🔑" },
    { label: "Xuất Excel / Báo cáo",     allowed: !!scope.can_export,          icon: "📊" },
    { label: "Bàn giao & khóa tài khoản", allowed: !!scope.can_handover,       icon: "🔄" },
  ];

  return (
    <div>
      {/* Welcome banner */}
      <div className="dashboard-welcome" style={{ background: cfg.gradient }}>
        <h2>{cfg.emoji} Xin chào, {user.full_name}!</h2>
        <p>{cfg.desc}</p>
        <div className="role-badge">🏷️ {user.role_label}</div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon indigo">📋</div>
          <div className="stat-info"><small>Phạm vi dữ liệu</small><strong>{scope.description?.split(".")[0] || user.role_label}</strong></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">🔑</div>
          <div className="stat-info"><small>Vai trò</small><strong>{user.role_label}</strong></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon violet">📧</div>
          <div className="stat-info"><small>Email đăng nhập</small><strong style={{ fontSize: "1rem", wordBreak: "break-all" }}>{user.email}</strong></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon amber">🔒</div>
          <div className="stat-info"><small>Phiên đăng nhập</small><strong style={{ fontSize: "1rem" }}>Đang hoạt động</strong></div>
        </div>
      </div>

      <div className="scope-grid">
        {/* Quyền dữ liệu (S1-05) */}
        <div className="scope-card">
          <h4>🛡️ Phân quyền dữ liệu (S1-05)</h4>
          <p style={{ fontSize: ".82rem", color: "var(--gray-500)", marginBottom: 12 }}>{scope.description}</p>
          {scopeItems.map(item => (
            <div key={item.label} className={`scope-item${item.allowed ? " allowed" : " denied"}`}>
              <span>{item.allowed ? "✅" : "❌"}</span>
              <span>{item.icon} {item.label}</span>
            </div>
          ))}
        </div>

        {/* Menu theo vai trò (S1-06) */}
        <div className="scope-card">
          <h4>📋 Menu theo vai trò (S1-06)</h4>
          <p style={{ fontSize: ".82rem", color: "var(--gray-500)", marginBottom: 12 }}>
            Menu hiển thị {menu.length} mục dành cho vai trò <strong>{user.role_label}</strong>.
          </p>
          {menu.map(item => (
            <div key={item.key} className="scope-item allowed" style={{ justifyContent: "space-between" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span>{item.icon}</span><span>{item.label}</span>
              </span>
              <code style={{ fontSize: ".72rem", color: "var(--gray-400)", background: "var(--gray-100)", padding: "2px 6px", borderRadius: 4 }}>{item.path}</code>
            </div>
          ))}
        </div>

        {/* Thông báo lỗi mẫu (S1-07) */}
        <div className="scope-card">
          <h4>⚠️ Thông báo lỗi rõ ràng (S1-07)</h4>
          <p style={{ fontSize: ".82rem", color: "var(--gray-500)", marginBottom: 12 }}>
            Mỗi trạng thái lỗi có thông báo tiếng Việt rõ ràng và hành động gợi ý.
          </p>
          <div className="alert alert-error" style={{ marginBottom: 8 }}>
            <span>⚠️</span><span>Email hoặc mật khẩu không đúng. (401)</span>
          </div>
          <div className="alert alert-warning" style={{ marginBottom: 8 }}>
            <span>⏳</span><span>Tài khoản bị khóa 15 phút sau 5 lần sai. (429)</span>
          </div>
          <div className="alert alert-info">
            <span>ℹ️</span><span>Phiên hết hạn → quay về trang đăng nhập. (401)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
