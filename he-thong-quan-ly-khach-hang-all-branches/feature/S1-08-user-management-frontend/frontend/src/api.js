const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
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
    const error = new Error(data.message || "Yêu cầu không thành công.");
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export function getUsers(filters = {}) {
  const params = new URLSearchParams();

  if (filters.search) params.set("q", filters.search);
  if (filters.group) params.set("group", filters.group);
  if (filters.role) params.set("role", filters.role);
  if (filters.status) params.set("status", filters.status);

  params.set("page", String(filters.page || 1));
  params.set("per_page", "20");

  return request(`/api/users?${params.toString()}`);
}

export function createUser(payload) {
  return request("/api/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUser(userId, payload) {
  return request(`/api/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function activateUser(token) {
  return request("/api/users/activate", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}
