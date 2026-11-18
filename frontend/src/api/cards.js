import { request } from "./client.js";

// Danh mục bài cho trang lướt, tải theo trang (lazy row)
export const listCatalog = (limit = 12, offset = 0) => request(`/cards?limit=${limit}&offset=${offset}`);

// Cả bộ 78 lá kèm details, tải một lần rồi dùng chung (lá rút ngẫu nhiên, lá trong lần bốc chỉ có tóm tắt)
let deck = null;
export const getDeck = () =>
  (deck ??= listCatalog(78, 0).catch((err) => {
    deck = null; // lỗi mạng: lần sau thử lại
    throw err;
  }));
