const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

let authToken = null;
export const setAuthToken = (token) => {
  authToken = token;
};

export async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Lỗi ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}
