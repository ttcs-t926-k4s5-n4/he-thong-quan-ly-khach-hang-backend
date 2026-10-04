import { useEffect, useState } from "react";
import { getCurrentUser, logout } from "./api";
import ChangePasswordForm from "./ChangePasswordForm";
import LoginForm from "./LoginForm";
import "./styles.css";

export default function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    getCurrentUser()
      .then((result) => setUser(result.user))
      .catch(() => setUser(null))
      .finally(() => setCheckingSession(false));
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  if (checkingSession) {
    return (
      <main className="page">
        <div className="loading-card">Đang kiểm tra phiên đăng nhập...</div>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="shell">
        <header className="topbar">
          <div>
            <span className="brand">CRM</span>
            <span className="separator">/</span>
            <span>S1-04 Change Password</span>
          </div>

          {user && (
            <button className="ghost-button" type="button" onClick={handleLogout}>
              Đăng xuất
            </button>
          )}
        </header>

        {user ? (
          <ChangePasswordForm user={user} />
        ) : (
          <LoginForm onLoggedIn={setUser} />
        )}
      </div>
    </main>
  );
}
