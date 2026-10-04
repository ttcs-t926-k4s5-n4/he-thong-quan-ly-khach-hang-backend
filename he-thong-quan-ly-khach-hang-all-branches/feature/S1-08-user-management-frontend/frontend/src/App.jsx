import { useEffect, useState } from "react";
import { createUser, getUsers, updateUser } from "./api";
import ActivationPage from "./ActivationPage";

const groups = [
  "Kinh doanh",
  "Kỹ thuật",
  "Kế toán",
  "Nhân sự",
  "Marketing",
];

const roles = [
  "Nhân viên kinh doanh",
  "Trưởng nhóm",
  "Kỹ thuật viên",
  "Kế toán",
  "Nhân sự",
  "Marketing",
];

const statuses = ["Đang hoạt động", "Chờ kích hoạt", "Tạm khóa"];

function resolveActivationToken() {
  if (window.location.pathname !== "/activate") return null;
  return new URLSearchParams(window.location.search).get("token");
}

function App() {
  const activationToken = resolveActivationToken();

  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [groupFilter, setGroupFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    pending: 0,
    roles: 0,
  });
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [message, setMessage] = useState("");
  const [activation, setActivation] = useState(null);

  async function loadUsers(nextPage = page) {
    setLoading(true);
    try {
      const result = await getUsers({
        search,
        group: groupFilter,
        role: roleFilter,
        status: statusFilter,
        page: nextPage,
      });

      setUsers(result.items || []);
      setPage(result.pagination?.page || 1);
      setTotalPages(result.pagination?.total_pages || 1);
      setTotalUsers(result.pagination?.total || 0);
      setStats(
        result.stats || {
          total: 0,
          active: 0,
          pending: 0,
          roles: 0,
        }
      );
    } catch (error) {
      showMessage(error.data?.message || "Không thể tải danh sách người dùng.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activationToken) {
      loadUsers(1);
    }
  }, [search, groupFilter, roleFilter, statusFilter]);

  function showMessage(text) {
    setMessage(text);
    window.setTimeout(() => setMessage(""), 3500);
  }

  async function saveUser(event) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const payload = {
      full_name: String(form.get("name") || "").trim(),
      email: String(form.get("email") || "").trim().toLowerCase(),
      group_name: String(form.get("group") || ""),
      role_name: String(form.get("role") || ""),
    };

    if (!payload.full_name || !payload.email) {
      showMessage("Vui lòng nhập đầy đủ thông tin.");
      return;
    }

    try {
      if (editingUser) {
        await updateUser(editingUser.id, payload);
        showMessage("Đã cập nhật tài khoản.");
      } else {
        const result = await createUser(payload);
        setActivation({
          email: payload.email,
          name: payload.full_name,
          message:
            result.message ||
            "Email kích hoạt kèm mật khẩu tạm đã được gửi.",
        });
      }

      setEditingUser(null);
      setShowForm(false);
      await loadUsers(1);
    } catch (error) {
      if (error.status === 409) {
        showMessage(
          error.data?.message ||
            "Email đã tồn tại. Vui lòng sử dụng email khác."
        );
      } else {
        showMessage(error.data?.message || "Không thể lưu tài khoản.");
      }
    }
  }

  function editUser(user) {
    setEditingUser(user);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingUser(null);
  }

  if (activationToken) {
    return <ActivationPage token={activationToken} />;
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logoIcon">✓</div>
          <div>
            <strong>CRM Admin</strong>
            <small>Hệ thống quản lý khách hàng</small>
          </div>
        </div>

        <div className="admin">
          <div className="adminAvatar">QT</div>
          <div>
            <strong>Quản trị viên</strong>
            <small>Quản trị hệ thống</small>
          </div>
        </div>
      </header>

      <main className="container">
        <div className="pageTitle">
          <div>
            <div className="label">S1-08 · QUẢN TRỊ NGƯỜI DÙNG</div>
            <h1>Tài khoản người dùng</h1>
            <p>
              Tạo, chỉnh sửa, tìm kiếm và quản lý tài khoản nhân viên trong hệ
              thống.
            </p>
          </div>

          <button
            className="primaryButton"
            onClick={() => {
              setEditingUser(null);
              setShowForm(true);
            }}
          >
            + Tạo tài khoản
          </button>
        </div>

        <div className="stats">
          <div className="stat">
            <span>👥</span>
            <div>
              <small>Tổng tài khoản</small>
              <strong>{stats.total}</strong>
            </div>
          </div>

          <div className="stat">
            <span>✓</span>
            <div>
              <small>Đang hoạt động</small>
              <strong>{stats.active}</strong>
            </div>
          </div>

          <div className="stat">
            <span>✉</span>
            <div>
              <small>Chờ kích hoạt</small>
              <strong>{stats.pending}</strong>
            </div>
          </div>

          <div className="stat">
            <span>🔑</span>
            <div>
              <small>Vai trò</small>
              <strong>{stats.roles}</strong>
            </div>
          </div>
        </div>

        <section className="box">
          <h3>🔎 Bộ lọc & tìm kiếm</h3>
          <div className="filters">
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Tìm theo tên, email hoặc nhóm..."
            />

            <select
              value={groupFilter}
              onChange={(event) => {
                setGroupFilter(event.target.value);
                setPage(1);
              }}
            >
              <option value="">Tất cả nhóm</option>
              {groups.map((group) => (
                <option key={group}>{group}</option>
              ))}
            </select>

            <select
              value={roleFilter}
              onChange={(event) => {
                setRoleFilter(event.target.value);
                setPage(1);
              }}
            >
              <option value="">Tất cả vai trò</option>
              {roles.map((role) => (
                <option key={role}>{role}</option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setPage(1);
              }}
            >
              <option value="">Tất cả trạng thái</option>
              {statuses.map((status) => (
                <option key={status}>{status}</option>
              ))}
            </select>
          </div>
        </section>

        <section className="box">
          <div className="tableHeader">
            <div>
              <h3>Danh sách người dùng</h3>
              <small>{totalUsers} tài khoản phù hợp</small>
            </div>
            <span>Hiển thị 20 dòng/trang</span>
          </div>

          <div className="tableContainer">
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
                  <tr>
                    <td colSpan="6">Đang tải dữ liệu...</td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="6">Không có tài khoản phù hợp.</td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="user">
                          <div className="avatar">
                            {user.full_name
                              .split(" ")
                              .slice(-2)
                              .map((part) => part[0])
                              .join("")}
                          </div>
                          <div>
                            <strong>{user.full_name}</strong>
                            <small>ID #{user.id}</small>
                          </div>
                        </div>
                      </td>
                      <td>{user.email}</td>
                      <td>{user.group_name}</td>
                      <td>
                        <span className="role">{user.role_name}</span>
                      </td>
                      <td>
                        <span
                          className={
                            "status " +
                            (user.status === "Đang hoạt động"
                              ? "active"
                              : user.status === "Chờ kích hoạt"
                                ? "pending"
                                : "locked")
                          }
                        >
                          ● {user.status}
                        </span>
                      </td>
                      <td>
                        <div className="actions">
                          <button
                            aria-label={`Chỉnh sửa ${user.full_name}`}
                            onClick={() => editUser(user)}
                          >
                            ✏
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span>
              Trang {page} / {totalPages}
            </span>
            <div>
              <button
                disabled={page === 1}
                onClick={() => {
                  const next = page - 1;
                  setPage(next);
                  loadUsers(next);
                }}
              >
                ←
              </button>

              {Array.from({ length: totalPages }, (_, index) => index + 1).map(
                (number) => (
                  <button
                    key={number}
                    className={page === number ? "current" : ""}
                    onClick={() => {
                      setPage(number);
                      loadUsers(number);
                    }}
                  >
                    {number}
                  </button>
                )
              )}

              <button
                disabled={page === totalPages}
                onClick={() => {
                  const next = page + 1;
                  setPage(next);
                  loadUsers(next);
                }}
              >
                →
              </button>
            </div>
          </div>
        </section>
      </main>

      {showForm && (
        <div className="overlay">
          <div className="modal">
            <div className="modalHeader">
              <div>
                <h2>
                  {editingUser ? "Chỉnh sửa tài khoản" : "Tạo tài khoản mới"}
                </h2>
                <p>Nhập thông tin tài khoản người dùng.</p>
              </div>
              <button onClick={closeForm}>✕</button>
            </div>

            <form onSubmit={saveUser}>
              <label>
                Họ và tên *
                <input
                  name="name"
                  defaultValue={editingUser?.full_name || ""}
                  placeholder="Nguyễn Văn A"
                />
              </label>

              <label>
                Email công ty *
                <input
                  name="email"
                  type="email"
                  defaultValue={editingUser?.email || ""}
                  placeholder="nhanvien@company.vn"
                />
              </label>

              <label>
                Nhóm *
                <select
                  name="group"
                  defaultValue={editingUser?.group_name || "Kinh doanh"}
                >
                  {groups.map((group) => (
                    <option key={group}>{group}</option>
                  ))}
                </select>
              </label>

              <label>
                Vai trò *
                <select
                  name="role"
                  defaultValue={
                    editingUser?.role_name || "Nhân viên kinh doanh"
                  }
                >
                  {roles.map((role) => (
                    <option key={role}>{role}</option>
                  ))}
                </select>
              </label>

              {!editingUser && (
                <div className="hint">
                  ✉ Sau khi tạo tài khoản, hệ thống sẽ sinh mật khẩu tạm và gửi
                  email kích hoạt tới email công ty.
                </div>
              )}

              <div className="modalButtons">
                <button type="button" onClick={closeForm}>
                  Hủy
                </button>
                <button className="primaryButton" type="submit">
                  {editingUser ? "Lưu thay đổi" : "Tạo tài khoản"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {activation && (
        <div className="overlay">
          <div className="modal successModal">
            <div className="successIcon">✓</div>
            <h2>Tạo tài khoản thành công</h2>
            <p>{activation.message}</p>
            <strong>{activation.email}</strong>

            <div className="emailBox">
              <h3>✉ Email kích hoạt đã được gửi</h3>
              <p>Xin chào {activation.name},</p>
              <p>
                Email có liên kết kích hoạt tài khoản và mật khẩu tạm. Mật khẩu
                tạm không hiển thị trên màn hình quản trị.
              </p>
            </div>

            <button
              className="primaryButton full"
              onClick={() => setActivation(null)}
            >
              Đã hiểu
            </button>
          </div>
        </div>
      )}

      {message && <div className="message">✓ {message}</div>}
    </div>
  );
}

export default App;
