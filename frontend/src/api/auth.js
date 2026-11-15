import { request } from "./client.js";

export const login = (email, password) => request("/auth/login", { method: "POST", body: { email, password } });
export const register = (email, password) => request("/auth/register", { method: "POST", body: { email, password } });
export const me = () => request("/auth/me");
