// App.jsx — SPA router dựa trên state (không cần react-router)
import { useEffect, useState } from "react";
import { apiMe } from "./api/index.js";

import LoginPage         from "./pages/LoginPage.jsx";
import ForgotPasswordPage from "./pages/ForgotPasswordPage.jsx";
import ResetPasswordPage  from "./pages/ResetPasswordPage.jsx";
import ActivationPage     from "./pages/ActivationPage.jsx";
import DashboardPage      from "./pages/DashboardPage.jsx";
import ChangePasswordPage from "./pages/ChangePasswordPage.jsx";
import UserManagementPage from "./pages/UserManagementPage.jsx";
import RoleManagementPage from "./pages/RoleManagementPage.jsx";
import Layout             from "./components/Layout.jsx";

// ── Parse URL path on load ────────────────────────────────────────────────────
function parseInitialRoute() {
  const path = window.location.pathname;
  const search = new URLSearchParams(window.location.search);

  if (path === "/activate")
    return { screen: "activation", token: search.get("token") || "" };

  const resetMatch = path.match(/^\/reset-password\/(.+)$/);
  if (resetMatch)
    return { screen: "reset-password", token: resetMatch[1] };

  return { screen: "login", token: "" };
}

// ── Loading splash ─────────────────────────────────────────────────────────────
function Splash() {
  return (
    <div style={{
      minHeight: "100vh", display: "grid", placeItems: "center",
      background: "linear-gradient(135deg,#312e81 0%,#7c3aed 100%)",
    }}>
      <div style={{ textAlign: "center", color: "white" }}>
        <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>💼</div>
        <h2 style={{ fontWeight: 800, marginBottom: 8 }}>CRM System</h2>
        <div className="spinner" style={{ margin: "16px auto 0", width: 32, height: 32, borderWidth: 3 }} />
      </div>
    </div>
  );
}

export default function App() {
  const initial = parseInitialRoute();

  const [screen, setScreen]   = useState(initial.screen); // login|forgot|reset-password|activation|app
  const [token, setToken]     = useState(initial.token);
  const [profile, setProfile] = useState(null);
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [checking, setChecking] = useState(true);

  // Check existing session on mount
  useEffect(() => {
    if (initial.screen === "activation" || initial.screen === "reset-password") {
      setChecking(false);
      return;
    }
    apiMe()
      .then(data => {
        setProfile(data);
        setScreen("app");
        setCurrentPage(resolveDefaultPage(data.user?.role));
      })
      .catch(() => { /* no session — stay on login */ })
      .finally(() => setChecking(false));
  }, []);

  function resolveDefaultPage(role) {
    return "dashboard";
  }

  function handleLoginSuccess(user, redirectUrl) {
    // Re-fetch full profile (includes scope + menu)
    apiMe().then(data => {
      setProfile(data);
      setScreen("app");
      setCurrentPage("dashboard");
    });
  }

  function handleLogout() {
    setProfile(null);
    setScreen("login");
    window.history.pushState({}, "", "/");
  }

  function handleSessionExpired() {
    setProfile(null);
    setScreen("login");
    window.history.pushState({}, "", "/");
  }

  function navigate(page) {
    setCurrentPage(page);
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  if (checking) return <Splash />;

  // URL-based special screens
  if (screen === "activation")
    return <ActivationPage token={token} onGoLogin={() => { setScreen("login"); window.history.pushState({}, "", "/"); }} />;

  if (screen === "reset-password")
    return <ResetPasswordPage token={token} onSuccess={() => { setScreen("login"); window.history.pushState({}, "", "/"); }} />;

  // Auth screens
  if (screen === "login")
    return <LoginPage onSuccess={handleLoginSuccess} onForgot={() => setScreen("forgot")} />;

  if (screen === "forgot")
    return <ForgotPasswordPage onBack={() => setScreen("login")} />;

  // App (authenticated)
  if (screen === "app" && profile) {
    const pageComponent = () => {
      switch (currentPage) {
        case "dashboard":        return <DashboardPage profile={profile} />;
        case "change-password":  return <ChangePasswordPage onSessionExpired={handleSessionExpired} />;
        case "users":            return <UserManagementPage onSessionExpired={handleSessionExpired} />;
        case "roles":            return <RoleManagementPage />;
        default:                 return <DashboardPage profile={profile} />;
      }
    };

    return (
      <Layout
        profile={profile}
        currentPage={currentPage}
        onNavigate={navigate}
        onLogout={handleLogout}
      >
        {pageComponent()}
      </Layout>
    );
  }

  return <Splash />;
}
