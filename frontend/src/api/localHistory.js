// Lịch sử các lần rút nhanh (lá hôm nay/tuần/tháng/năm, Yes/No): rút ngay trên trình duyệt nên chỉ lưu trên thiết bị.
// Mục: { id, kind: "day"|"week"|"month"|"year"|"yesno", period?, slug, reversed, question?, created_at }
const KEY = "tarot_local_history";
const MAX = 200;

export function loadLocalHistory() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? [];
  } catch {
    return [];
  }
}

const save = (list) => {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* trình duyệt chặn lưu: bỏ qua */
  }
};

export function addLocalHistory(entry) {
  save([{ id: `l${Date.now()}`, created_at: new Date().toISOString(), ...entry }, ...loadLocalHistory()]);
}

export function removeLocalHistory(id) {
  save(loadLocalHistory().filter((e) => e.id !== id));
}
