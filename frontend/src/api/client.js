import { mockRequest } from "../mock/mockServer.js";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
// Mặc định dùng dữ liệu giả; đặt VITE_USE_MOCK=false trong .env để gọi backend thật
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

let authToken = null;
let onUnauthorized = null;
export const setAuthToken = (token) => {
  authToken = token;
};
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

export async function request(path, { method = "GET", body } = {}) {
  if (USE_MOCK) return mockRequest(path, { method, body });
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Không kết nối được máy chủ. Kiểm tra mạng hoặc thử lại sau.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 && authToken && onUnauthorized) onUnauthorized();
    // FastAPI 422 mặc định trả detail là mảng
    const detail = Array.isArray(err.detail) ? err.detail.map((d) => d.msg).join("; ") : err.detail;
    const error = new Error(
      detail ?? (res.status === 403 ? "Bạn không có quyền thực hiện thao tác này." : `Lỗi ${res.status}`)
    );
    error.status = res.status;
    throw error;
  }
  return res.status === 204 ? null : res.json();
}
