import { request } from "./client.js";

// interpret=false: backend trả lá ngay (ai_status "pending"), gọi reinterpret sau để lấy lời giải
export const createReading = (spread_id, question, interpret = true) =>
  request(`/readings${interpret ? "" : "?interpret=false"}`, { method: "POST", body: { spread_id, question } });
export const reinterpret = (id) => request(`/readings/${id}/interpret`, { method: "POST" });
export const listReadings = (limit = 20, offset = 0) => request(`/readings?limit=${limit}&offset=${offset}`);
export const getReading = (id) => request(`/readings/${id}`);
export const rateReading = (id, accuracy) => request(`/readings/${id}/rating`, { method: "PUT", body: { accuracy } });
export const deleteReading = (id) => request(`/readings/${id}`, { method: "DELETE" });
