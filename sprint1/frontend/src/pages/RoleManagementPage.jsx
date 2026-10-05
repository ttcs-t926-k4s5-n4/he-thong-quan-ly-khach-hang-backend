// RoleManagementPage.jsx — S1-09 (quản lý vai trò & nhóm kinh doanh)
import { useState } from "react";

const ROLE_DEFINITIONS = [
  {
    code: "admin",
    label: "Quản trị hệ thống",
    icon: "🛡️",
    color: "#4f46e5",
    bg: "#eef2ff",
    description: "Toàn quyền truy cập và quản lý hệ thống.",
    permissions: ["Quản lý tài khoản người dùng", "Phân quyền vai trò", "Xem toàn bộ dữ liệu", "Bàn giao & khóa tài khoản", "Xuất báo cáo", "Cấu hình hệ thống"],
  },
  {
    code: "manager",
    label: "Giám đốc kinh doanh",
    icon: "📊",
    color: "#0369a1",
    bg: "#e0f2fe",
    description: "Xem dữ liệu nhóm và toàn công ty, xuất báo cáo.",
    permissions: ["Xem dữ liệu của mình", "Xem dữ liệu nhóm", "Xem toàn bộ khách hàng", "Xuất Excel/Báo cáo", "Xem hoạt động bán hàng"],
  },
  {
    code: "employee",
    label: "Nhân viên kinh doanh",
    icon: "👤",
    color: "#047857",
    bg: "#d1fae5",
    description: "Quản lý dữ liệu khách hàng của chính mình.",
    permissions: ["Xem & sửa dữ liệu của mình", "Thêm khách hàng mới", "Cập nhật cơ hội", "Ghi hoạt động"],
  },
];

const BUSINESS_GROUPS = [
  { id: 1, name: "Kinh doanh Miền Bắc",  manager: "Nguyễn Văn A", members: 8,  region: "Hà Nội" },
  { id: 2, name: "Kinh doanh Miền Nam",   manager: "Trần Thị B",   members: 12, region: "TP.HCM" },
  { id: 3, name: "Kinh doanh Miền Trung", manager: "Lê Văn C",     members: 5,  region: "Đà Nẵng" },
  { id: 4, name: "Kỹ thuật",             manager: "Phạm Thị D",   members: 6,  region: "Toàn quốc" },
  { id: 5, name: "Marketing",            manager: "Hoàng Văn E",  members: 4,  region: "Toàn quốc" },
];

const RULES = [
  { icon: "🛡️", text: "Trưởng nhóm phải thuộc một nhóm kinh doanh cụ thể." },
  { icon: "🚫", text: "Quản trị viên không thể tự thu hồi vai trò Quản trị của chính mình." },
  { icon: "🔄", text: "Một người dùng có thể giữ nhiều vai trò đồng thời." },
  { icon: "✅", text: "Kiểm tra tự động đảm bảo nhân viên A không thể truy cập dữ liệu nhân viên B." },
];

export default function RoleManagementPage() {
  const [activeTab, setActiveTab] = useState("roles");

  return (
    <div>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 24, background: "white", padding: 6, borderRadius: 12, border: "1px solid var(--gray-200)", width: "fit-content" }}>
        {[
          { key: "roles",  label: "🔑 Vai trò hệ thống" },
          { key: "groups", label: "👥 Nhóm kinh doanh" },
          { key: "rules",  label: "📋 Quy tắc phân quyền" },
        ].map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            style={{
              padding: "8px 18px", border: "none", borderRadius: 8, cursor: "pointer",
              fontWeight: 600, fontSize: ".88rem", fontFamily: "var(--font)",
              background: activeTab === t.key ? "var(--indigo-600)" : "transparent",
              color: activeTab === t.key ? "white" : "var(--gray-600)",
              transition: "all .15s ease",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Roles tab */}
      {activeTab === "roles" && (
        <div style={{ display: "grid", gap: 16 }}>
          {ROLE_DEFINITIONS.map(role => (
            <div className="card" key={role.code}>
              <div className="card-body">
                <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
                  <div style={{ width: 52, height: 52, borderRadius: 14, background: role.bg, display: "grid", placeItems: "center", fontSize: "1.5rem", flexShrink: 0 }}>
                    {role.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700 }}>{role.label}</h3>
                      <span style={{ background: role.bg, color: role.color, padding: "2px 10px", borderRadius: 20, fontSize: ".75rem", fontWeight: 700 }}>
                        {role.code}
                      </span>
                    </div>
                    <p style={{ color: "var(--gray-500)", fontSize: ".88rem", marginBottom: 12 }}>{role.description}</p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {role.permissions.map(p => (
                        <span key={p} style={{ display: "inline-flex", alignItems: "center", gap: 4, background: "var(--gray-50)", border: "1px solid var(--gray-200)", borderRadius: 6, padding: "4px 10px", fontSize: ".78rem", color: "var(--gray-700)" }}>
                          ✓ {p}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Groups tab */}
      {activeTab === "groups" && (
        <div className="card">
          <div className="card-header">
            <h3>Nhóm kinh doanh</h3>
            <span style={{ fontSize: ".82rem", color: "var(--gray-500)" }}>{BUSINESS_GROUPS.length} nhóm</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>TÊN NHÓM</th>
                  <th>TRƯỞNG NHÓM</th>
                  <th>KHU VỰC</th>
                  <th>THÀNH VIÊN</th>
                </tr>
              </thead>
              <tbody>
                {BUSINESS_GROUPS.map(g => (
                  <tr key={g.id}>
                    <td style={{ color: "var(--gray-400)", fontWeight: 600 }}>{g.id}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 36, height: 36, borderRadius: 10, background: "var(--indigo-50)", display: "grid", placeItems: "center", fontSize: "1.1rem" }}>👥</div>
                        <strong>{g.name}</strong>
                      </div>
                    </td>
                    <td>{g.manager}</td>
                    <td><span className="badge badge-role">📍 {g.region}</span></td>
                    <td>
                      <span style={{ fontWeight: 700, color: "var(--indigo-600)" }}>{g.members}</span>
                      <span style={{ color: "var(--gray-400)", fontSize: ".82rem" }}> người</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rules tab */}
      {activeTab === "rules" && (
        <div style={{ display: "grid", gap: 16, maxWidth: 720 }}>
          <div className="card">
            <div className="card-header"><h3>📋 Quy tắc phân quyền (S1-09)</h3></div>
            <div className="card-body">
              <p style={{ color: "var(--gray-500)", fontSize: ".9rem", marginBottom: 20 }}>
                Các quy tắc này được kiểm tra tự động ở backend mỗi khi cập nhật vai trò.
              </p>
              {RULES.map((r, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "14px 0", borderBottom: i < RULES.length - 1 ? "1px solid var(--gray-100)" : "none" }}>
                  <span style={{ fontSize: "1.3rem" }}>{r.icon}</span>
                  <p style={{ color: "var(--gray-700)", fontSize: ".9rem", lineHeight: 1.6 }}>{r.text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="alert alert-info">
            <span>ℹ️</span>
            <span>
              Backend (S1-09) sử dụng FastAPI + SQLAlchemy để validate các quy tắc phân quyền. Trong project tích hợp này, quy tắc được tích hợp vào Flask backend thống nhất.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
