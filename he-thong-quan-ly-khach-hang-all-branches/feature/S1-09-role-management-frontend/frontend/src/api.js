const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const CURRENT_ADMIN_ID =
  Number(import.meta.env.VITE_CURRENT_ADMIN_ID || "1");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Current-User-Id": String(CURRENT_ADMIN_ID),
      ...(options.headers || {}),
    },
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const error = new Error(
      data.detail || data.message || "Yêu cầu không thành công."
    );
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const getUsers = () => request("/api/users");
export const getRoles = () => request("/api/roles");
export const getBusinessGroups = () => request("/api/business-groups");

export const updateRoleAssignment = (userId, payload) =>
  request(`/api/users/${userId}/role-assignment`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
