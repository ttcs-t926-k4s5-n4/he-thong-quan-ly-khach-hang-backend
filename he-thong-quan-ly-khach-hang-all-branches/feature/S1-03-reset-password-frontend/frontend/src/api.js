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

export function requestPasswordReset(email) {
  return request("/api/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function inspectResetToken(token) {
  return request(`/api/auth/reset-password/${encodeURIComponent(token)}`, {
    method: "GET",
  });
}

export function resetPassword(token, password, confirmation) {
  return request(`/api/auth/reset-password/${encodeURIComponent(token)}`, {
    method: "POST",
    body: JSON.stringify({
      password,
      password_confirmation: confirmation,
    }),
  });
}
