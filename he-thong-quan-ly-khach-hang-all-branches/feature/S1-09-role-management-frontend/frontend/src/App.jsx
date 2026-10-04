import { useEffect, useMemo, useState } from "react";
import {
  getBusinessGroups,
  getRoles,
  getUsers,
  updateRoleAssignment,
} from "./api";
import "./styles.css";

function roleNames(user) {
  return (user.roles || []).map((role) => role.name).join(", ") || "Chưa gán";
}

export default function App() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [groups, setGroups] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const teamLeaderRole = useMemo(
    () => roles.find((role) => role.code === "TEAM_LEADER"),
    [roles]
  );

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [userData, roleData, groupData] = await Promise.all([
        getUsers(),
        getRoles(),
        getBusinessGroups(),
      ]);
      setUsers(userData);
      setRoles(roleData);
      setGroups(groupData);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function openEditor(user) {
    setSelectedUser(user);
    setSelectedRoleIds((user.roles || []).map((role) => role.id));
    setSelectedGroupId(user.business_group?.id || "");
    setMessage("");
    setError("");
  }

  function toggleRole(roleId) {
    setSelectedRoleIds((current) =>
      current.includes(roleId)
        ? current.filter((id) => id !== roleId)
        : [...current, roleId]
    );
  }

  async function saveAssignment() {
    if (!selectedUser) return;

    const hasTeamLeader =
      teamLeaderRole && selectedRoleIds.includes(teamLeaderRole.id);

    if (hasTeamLeader && !selectedGroupId) {
      setError(
        "Người giữ vai trò Trưởng nhóm phải được gán vào một nhóm kinh doanh cụ thể."
      );
      return;
    }

    try {
      setError("");
      const result = await updateRoleAssignment(selectedUser.id, {
        role_ids: selectedRoleIds,
        business_group_id: selectedGroupId
          ? Number(selectedGroupId)
          : null,
      });
      setMessage(result.message || "Đã cập nhật vai trò và nhóm kinh doanh.");
      await loadData();
      setSelectedUser(null);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brandMark">CRM</span>
          <div>
            <strong>Hệ thống quản lý khách hàng</strong>
            <small>S1-09 · Quản lý vai trò và nhóm kinh doanh</small>
          </div>
        </div>
        <div className="currentAdmin">
          <strong>Quản trị viên hiện tại</strong>
          <span>ID 1</span>
        </div>
      </header>

      <main className="container">
        <section className="intro">
          <div>
            <p className="eyebrow">S1-09 · QUẢN TRỊ HỆ THỐNG</p>
            <h1>Gán vai trò và nhóm kinh doanh</h1>
            <p>
              Một người dùng có thể giữ nhiều vai trò cùng lúc. Trưởng nhóm bắt
              buộc phải thuộc một nhóm kinh doanh cụ thể.
            </p>
          </div>
        </section>

        {message && <div className="success">{message}</div>}
        {error && <div className="error">{error}</div>}

        <section className="panel">
          <div className="panelHeader">
            <div>
              <h2>Danh sách người dùng</h2>
              <p>Chọn một người dùng để cập nhật vai trò và nhóm kinh doanh.</p>
            </div>
          </div>

          {loading ? (
            <div className="empty">Đang tải dữ liệu...</div>
          ) : (
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>Người dùng</th>
                    <th>Email</th>
                    <th>Vai trò</th>
                    <th>Nhóm kinh doanh</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <strong>{user.full_name}</strong>
                        <small>ID {user.id}</small>
                      </td>
                      <td>{user.email}</td>
                      <td>{roleNames(user)}</td>
                      <td>{user.business_group?.name || "Chưa gán"}</td>
                      <td>
                        <button
                          className="secondaryButton"
                          onClick={() => openEditor(user)}
                        >
                          Gán vai trò
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {selectedUser && (
        <div className="overlay">
          <section className="modal">
            <div className="modalHeader">
              <div>
                <p className="eyebrow">CẬP NHẬT PHÂN QUYỀN</p>
                <h2>{selectedUser.full_name}</h2>
                <p>{selectedUser.email}</p>
              </div>
              <button
                className="closeButton"
                onClick={() => setSelectedUser(null)}
              >
                ×
              </button>
            </div>

            <div className="field">
              <label>Vai trò</label>
              <p className="help">
                Có thể chọn nhiều vai trò cùng lúc.
              </p>
              <div className="roleGrid">
                {roles.map((role) => (
                  <label className="checkCard" key={role.id}>
                    <input
                      type="checkbox"
                      checked={selectedRoleIds.includes(role.id)}
                      onChange={() => toggleRole(role.id)}
                    />
                    <span>
                      <strong>{role.name}</strong>
                      <small>{role.code}</small>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="field">
              <label htmlFor="businessGroup">Nhóm kinh doanh</label>
              <select
                id="businessGroup"
                value={selectedGroupId}
                onChange={(event) => setSelectedGroupId(event.target.value)}
              >
                <option value="">Chưa gán nhóm</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
              <p className="help">
                Nếu người dùng giữ vai trò Trưởng nhóm thì bắt buộc phải chọn
                một nhóm kinh doanh.
              </p>
            </div>

            <div className="warning">
              Quản trị viên không thể tự thu hồi vai trò Quản trị của chính mình.
            </div>

            <div className="modalActions">
              <button
                className="cancelButton"
                onClick={() => setSelectedUser(null)}
              >
                Hủy
              </button>
              <button className="primaryButton" onClick={saveAssignment}>
                Lưu thay đổi
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
