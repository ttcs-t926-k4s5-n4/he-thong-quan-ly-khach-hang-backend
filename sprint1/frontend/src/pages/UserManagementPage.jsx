// UserManagementPage.jsx — S1-08
import { useEffect, useState } from "react";
import { apiGetUsers, apiCreateUser, apiUpdateUser } from "../api/index.js";

const GROUPS = ["Kinh doanh", "Kỹ thuật", "Kế toán", "Nhân sự", "Marketing"];
const ROLES  = ["Nhân viên kinh doanh", "Trưởng nhóm", "Kỹ thuật viên", "Kế toán", "Nhân sự", "Marketing"];
const STATUSES = ["Đang hoạt động", "Chờ kích hoạt", "Tạm khóa"];

function initials(name = "") {
  return name.split(" ").slice(-2).map(p => p[0]).join("").toUpperCase();
}

export default function UserManagementPage({ onSessionExpired }) {
  const [users, setUsers]           = useState([]);
  const [stats, setStats]           = useState({ total: 0, active: 0, pending: 0, roles: 0 });
  const [pagination, setPagination] = useState({ page: 1, total_pages: 1, total: 0 });
  const [filters, setFilters]       = useState({ q: "", group: "", role: "", status: "" });
  const [loading, setLoading]       = useState(false);

  const [showForm, setShowForm]     = useState(false);
  const [editing, setEditing]       = useState(null);
  const [formData, setFormData]     = useState({ full_name: "", email: "", group_name: "Kinh doanh", role_name: "Nhân viên kinh doanh" });
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving]         = useState(false);

  const [toast, setToast]           = useState(null);
  const [activation, setActivation] = useState(null);

  function showToast(msg, type = "success") {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  }

  async function load(page = 1) {
    setLoading(true);
    try {
      const res = await apiGetUsers({ ...filters, page });
      setUsers(res.items || []);
      setStats(res.stats || {});
      setPagination(res.pagination || {});
    } catch (err) {
      if (err.status === 401) { onSessionExpired?.(); return; }
      showToast(err.data?.message || "Không thể tải danh sách.", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(1); }, [filters]);

  function openCreate() {
    setEditing(null);
    setFormData({ full_name: "", email: "", group_name: "Kinh doanh", role_name: "Nhân viên kinh doanh" });
    setFormErrors({});
    setShowForm(true);
  }
  function openEdit(user) {
    setEditing(user);
    setFormData({ full_name: user.full_name, email: user.email, group_name: user.group_name, role_name: user.role_name });
    setFormErrors({});
    setShowForm(true);
  }

  async function handleSave(e) {
    e.preventDefault();
    setFormErrors({}); setSaving(true);
    try {
      if (editing) {
        await apiUpdateUser(editing.id, formData);
        showToast("Đã cập nhật tài khoản.");
      } else {
        const res = await apiCreateUser(formData);
        setActivation({ email: formData.email, name: formData.full_name, message: res.message });
      }
      setShowForm(false);
      load(1);
    } catch (err) {
      if (err.status === 401) { onSessionExpired?.(); return; }
      if (err.data?.errors) setFormErrors(err.data.errors);
      else showToast(err.data?.message || "Lưu thất bại.", "error");
    } finally {
      setSaving(false);
    }
  }

  function setFilter(key, val) { setFilters(f => ({ ...f, [key]: val })); }
  function setField(key, val)  { setFormData(f => ({ ...f, [key]: val })); setFormErrors(e => ({ ...e, [key]: undefined })); }

  const totalPages = pagination.total_pages || 1;
  const currentPage = pagination.page || 1;

  return (
    <div>
      {/* Stats */}
      <div className="stats-grid">
        {[
          { icon: "👥", label: "Tổng tài khoản",   val: stats.total,   cls: "indigo" },
          { icon: "✅", label: "Đang hoạt động",    val: stats.active,  cls: "green"  },
          { icon: "✉️", label: "Chờ kích hoạt",     val: stats.pending, cls: "amber"  },
          { icon: "🔑", label: "Loại vai trò",       val: stats.roles,   cls: "violet" },
        ].map(s => (
          <div className="stat-card" key={s.label}>
            <div className={`stat-icon ${s.cls}`}>{s.icon}</div>
            <div className="stat-info"><small>{s.label}</small><strong>{s.val ?? 0}</strong></div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ paddingTop: 16, paddingBottom: 16 }}>
          <div className="filters">
            <input className="filter-input" value={filters.q}
              onChange={e => setFilter("q", e.target.value)}
              placeholder="🔍 Tìm tên, email, nhóm..." />
            <select className="filter-select" value={filters.group} onChange={e => setFilter("group", e.target.value)}>
              <option value="">Tất cả nhóm</option>
              {GROUPS.map(g => <option key={g}>{g}</option>)}
            </select>
            <select className="filter-select" value={filters.role} onChange={e => setFilter("role", e.target.value)}>
              <option value="">Tất cả vai trò</option>
              {ROLES.map(r => <option key={r}>{r}</option>)}
            </select>
            <select className="filter-select" value={filters.status} onChange={e => setFilter("status", e.target.value)}>
              <option value="">Tất cả trạng thái</option>
              {STATUSES.map(s => <option key={s}>{s}</option>)}
            </select>
            <button className="btn btn-primary btn-sm" onClick={openCreate}>+ Tạo tài khoản</button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3>Danh sách tài khoản</h3>
            <p style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>{pagination.total ?? 0} tài khoản phù hợp</p>
          </div>
          <span style={{ fontSize: ".8rem", color: "var(--gray-400)" }}>Hiển thị 20 dòng/trang</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>NGƯỜI DÙNG</th>
                <th>EMAIL</th>
                <th>NHÓM</th>
                <th>VAI TRÒ</th>
                <th>TRẠNG THÁI</th>
                <th>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: "center", padding: 40, color: "var(--gray-400)" }}>
                  <div className="spinner spinner-dark" style={{ margin: "0 auto 8px" }} />
                  Đang tải...
                </td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={6}>
                  <div className="empty-state">
                    <div className="icon">👤</div>
                    <p>Không tìm thấy tài khoản phù hợp.</p>
                  </div>
                </td></tr>
              ) : users.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className="user-cell">
                      <div className="user-avatar">{initials(u.full_name)}</div>
                      <div><strong>{u.full_name}</strong><small>ID #{u.id}</small></div>
                    </div>
                  </td>
                  <td style={{ color: "var(--gray-600)" }}>{u.email}</td>
                  <td>{u.group_name}</td>
                  <td><span className="badge badge-role">{u.role_name}</span></td>
                  <td>
                    <span className={`badge badge-${u.status === "Đang hoạt động" ? "active" : u.status === "Chờ kích hoạt" ? "pending" : "locked"}`}>
                      ● {u.status}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm btn-icon" title="Chỉnh sửa" onClick={() => openEdit(u)}>✏️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="pagination">
          <span>Trang {currentPage} / {totalPages}</span>
          <div className="pagination-btns">
            <button className="page-btn" disabled={currentPage === 1} onClick={() => load(currentPage - 1)}>‹</button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map(n => (
              <button key={n} className={`page-btn${n === currentPage ? " active" : ""}`} onClick={() => load(n)}>{n}</button>
            ))}
            <button className="page-btn" disabled={currentPage === totalPages} onClick={() => load(currentPage + 1)}>›</button>
          </div>
        </div>
      </div>

      {/* Create / Edit Modal */}
      {showForm && (
        <div className="overlay" onClick={e => e.target === e.currentTarget && setShowForm(false)}>
          <div className="modal">
            <div className="modal-header">
              <div>
                <h2>{editing ? "Chỉnh sửa tài khoản" : "Tạo tài khoản mới"}</h2>
                <p>{editing ? "Cập nhật thông tin người dùng." : "Hệ thống sẽ gửi email kích hoạt kèm mật khẩu tạm."}</p>
              </div>
              <button className="modal-close" onClick={() => setShowForm(false)}>✕</button>
            </div>
            <form onSubmit={handleSave}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Họ và tên *</label>
                  <input className={`form-input${formErrors.full_name ? " error" : ""}`}
                    value={formData.full_name} onChange={e => setField("full_name", e.target.value)}
                    placeholder="Nguyễn Văn A" required />
                  {formErrors.full_name && <div className="field-error">{formErrors.full_name}</div>}
                </div>
                <div className="form-group">
                  <label>Email công ty *</label>
                  <input className={`form-input${formErrors.email ? " error" : ""}`}
                    type="email" value={formData.email} onChange={e => setField("email", e.target.value)}
                    placeholder="nhanvien@company.vn" required disabled={!!editing} />
                  {formErrors.email && <div className="field-error">{formErrors.email}</div>}
                </div>
                <div className="form-group">
                  <label>Nhóm *</label>
                  <select className="form-input" value={formData.group_name} onChange={e => setField("group_name", e.target.value)}>
                    {GROUPS.map(g => <option key={g}>{g}</option>)}
                  </select>
                  {formErrors.group_name && <div className="field-error">{formErrors.group_name}</div>}
                </div>
                <div className="form-group">
                  <label>Vai trò *</label>
                  <select className="form-input" value={formData.role_name} onChange={e => setField("role_name", e.target.value)}>
                    {ROLES.map(r => <option key={r}>{r}</option>)}
                  </select>
                  {formErrors.role_name && <div className="field-error">{formErrors.role_name}</div>}
                </div>
                {!editing && (
                  <div className="alert alert-info">
                    <span>✉️</span>
                    <span>Sau khi tạo, hệ thống sinh mật khẩu tạm và gửi email kích hoạt. Mật khẩu tạm không hiển thị trên màn hình.</span>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Hủy</button>
                <button type="submit" className="btn btn-primary" style={{ width: "auto" }} disabled={saving}>
                  {saving ? <><span className="spinner" /> Đang lưu...</> : editing ? "Lưu thay đổi" : "Tạo tài khoản"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Activation success modal */}
      {activation && (
        <div className="overlay">
          <div className="modal" style={{ textAlign: "center" }}>
            <div className="modal-body" style={{ padding: "40px 32px" }}>
              <div style={{ fontSize: "3rem", marginBottom: 16 }}>✅</div>
              <h2 style={{ marginBottom: 8 }}>Tạo tài khoản thành công!</h2>
              <p style={{ color: "var(--gray-600)", marginBottom: 16 }}>{activation.message}</p>
              <div style={{ background: "var(--gray-50)", border: "1px solid var(--gray-200)", borderRadius: 12, padding: "16px", marginBottom: 20 }}>
                <p style={{ fontSize: ".85rem", color: "var(--gray-500)", marginBottom: 6 }}>Email kích hoạt đã gửi tới:</p>
                <strong>{activation.email}</strong>
                <p style={{ fontSize: ".82rem", color: "var(--gray-400)", marginTop: 8 }}>
                  Xin chào <strong>{activation.name}</strong>, email có liên kết kích hoạt và mật khẩu tạm.
                </p>
              </div>
              <button className="btn btn-primary" onClick={() => setActivation(null)}>Đã hiểu</button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && <div className={`toast ${toast.type}`}>{toast.type === "success" ? "✅" : "❌"} {toast.msg}</div>}
    </div>
  );
}
