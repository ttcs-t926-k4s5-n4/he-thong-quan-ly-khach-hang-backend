// api/index.js — Tất cả API calls cho Sprint 1
const BASE = "/api"; // Proxy qua vite.config.js → http://127.0.0.1:5000

async function _request(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || "Lỗi không xác định.");
    err.data   = data;
    err.status = res.status;
    throw err;
  }
  return data;
}

const get  = (path)       => _request("GET",  path);
const post = (path, body) => _request("POST", path, body);
const put  = (path, body) => _request("PUT",  path, body);

// ─── Health ─────────────────────────────────────────────────────────────────
export const checkHealth = () => get("/health");

// ─── Auth (S1-01, S1-02) ────────────────────────────────────────────────────
export const apiLogin  = (email, password) => post("/auth/login",  { email, password });
export const apiMe     = ()                => get("/auth/me");
export const apiLogout = ()                => post("/auth/logout");

// ─── Reset password (S1-03) ─────────────────────────────────────────────────
export const apiForgotPassword    = (email)         => post("/auth/forgot-password", { email });
export const apiCheckResetToken   = (token)         => get(`/auth/reset-password/${token}`);
export const apiDoResetPassword   = (token, payload) => post(`/auth/reset-password/${token}`, payload);

// ─── Change password (S1-04) ────────────────────────────────────────────────
export const apiChangePassword = (payload) => post("/account/change-password", payload);

// ─── User management (S1-08) ────────────────────────────────────────────────
export const apiGetUsers      = (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== "" && v !== undefined)
  ).toString();
  return get(`/users${qs ? "?" + qs : ""}`);
};
export const apiCreateUser    = (payload)  => post("/users",           payload);
export const apiUpdateUser    = (id, body) => put(`/users/${id}`,      body);
export const apiActivateUser  = (token)    => post("/users/activate",  { token });
