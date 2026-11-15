import { request } from "./client.js";

export const createReading = (spread_id, question) => request("/readings", { method: "POST", body: { spread_id, question } });
export const reinterpret = (id) => request(`/readings/${id}/interpret`, { method: "POST" });
export const listReadings = (limit = 20, offset = 0) => request(`/readings?limit=${limit}&offset=${offset}`);
export const getReading = (id) => request(`/readings/${id}`);
export const deleteReading = (id) => request(`/readings/${id}`, { method: "DELETE" });
