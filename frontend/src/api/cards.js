import { request } from "./client.js";

// Danh mục bài cho trang lướt, tải theo trang (lazy row)
export const listCatalog = (limit = 12, offset = 0) => request(`/cards?limit=${limit}&offset=${offset}`);
