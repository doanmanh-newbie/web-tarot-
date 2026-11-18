// API giả chạy ngay trong trình duyệt, trả dữ liệu đúng định dạng docs/api-contract.md.
// Dùng để test giao diện khi chưa chạy backend. Dữ liệu lưu ở localStorage của trình duyệt.
// shortcut: không kiểm tra token/quyền như backend thật; khi test tích hợp đặt VITE_USE_MOCK=false.
import rawCards from "./cards.json";
import rawSpreads from "./spreads.json";

const KEY = "tarot_mock_db";
const DISCLAIMER = "Nội dung chỉ mang tính giải trí và tham khảo, không thay thế lời khuyên của chuyên gia.";
const USER = { id: 1, email: "demo@tarot.local", role: "admin" };

const baseCards = rawCards.map((c, i) => ({ id: i + 1, ...c }));
const spreads = rawSpreads.map((s, i) => ({
  id: i + 1,
  slug: s.slug,
  name: s.name,
  description: s.description,
  card_count: s.positions.length,
  positions: s.positions.map((p, index) => ({ index, ...p })),
}));

const hoursAgo = (h) => new Date(Date.now() - h * 3600_000).toISOString();

// Lịch sử mẫu có sẵn: 2 lần đã diễn giải, 1 lần AI lỗi để test nút "Giải lại"
function seedDb() {
  const db = { nextId: 4, cardEdits: {}, readings: [] };
  const samples = [
    [3, "Mối quan hệ với nhóm bạn thân sắp tới ra sao?", [[18, false], [34, true], [7, false], [50, false], [20, true]], "failed", 72],
    [2, "Công việc sắp tới của tôi thế nào?", [[1, false], [11, true], [20, false]], "done", 26],
    [1, "Hôm nay tôi nên chú ý điều gì?", [[18, false]], "done", 2],
  ];
  samples.forEach(([spread_id, question, cards, status, h], i) => {
    const r = {
      id: i + 1,
      spread_id,
      question,
      created_at: hoursAgo(h),
      ai_status: status,
      ai_interpretation: null,
      cards: cards.map(([card_id, is_reversed]) => ({ card_id, is_reversed })),
    };
    if (status === "done") r.ai_interpretation = interpret(db, r);
    db.readings.push(r);
  });
  return db;
}

function loadDb() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    if (saved?.readings) return saved;
  } catch {
    /* localStorage bị chặn hoặc hỏng: tạo lại */
  }
  return seedDb();
}
let db = loadDb();
const save = () => {
  try {
    localStorage.setItem(KEY, JSON.stringify(db));
  } catch {
    /* ignore */
  }
};

function card(dbState, id) {
  return { ...baseCards[id - 1], ...dbState.cardEdits[id] };
}
function meaning(c, reversed) {
  return reversed ? c.reversed_meaning : c.upright_meaning;
}

function interpret(dbState, r) {
  const spread = spreads[r.spread_id - 1];
  const lines = [`Với câu hỏi "${r.question}", kiểu trải bài "${spread.name}" cho thấy:`];
  r.cards.forEach((rc, i) => {
    const c = card(dbState, rc.card_id);
    lines.push(`\n• ${spread.positions[i].label}: ${c.name_vi} (${rc.is_reversed ? "ngược" : "xuôi"}). ${meaning(c, rc.is_reversed)}`);
  });
  lines.push("\nHãy xem đây là gợi ý để suy ngẫm, không phải lời tiên đoán chắc chắn. (Dữ liệu giả, không dùng AI)");
  return lines.join("\n");
}

function toResponse(r) {
  const spread = spreads[r.spread_id - 1];
  return {
    id: r.id,
    spread: { id: spread.id, name: spread.name },
    question: r.question,
    created_at: r.created_at,
    ai_status: r.ai_status,
    ai_interpretation: r.ai_interpretation,
    cards: r.cards.map((rc, i) => {
      const c = card(db, rc.card_id);
      return {
        position_index: i,
        position_label: spread.positions[i].label,
        is_reversed: rc.is_reversed,
        meaning: meaning(c, rc.is_reversed),
        card: { id: c.id, slug: c.slug, name: c.name, name_vi: c.name_vi, image_url: c.image_url },
      };
    }),
    disclaimer: DISCLAIMER,
  };
}

function fail(status, detail) {
  const err = new Error(detail);
  err.status = status;
  throw err;
}

function quota() {
  const resets = new Date();
  resets.setHours(24, 0, 0, 0);
  const today = new Date().toDateString();
  const used = db.readings.filter((r) => new Date(r.created_at).toDateString() === today).length;
  return { limit: null, used, remaining: null, resets_at: resets.toISOString(), unlimited: true };
}

function findReading(id) {
  return db.readings.find((r) => r.id === Number(id)) ?? fail(404, "Không tìm thấy lần bốc bài này.");
}

function drawCards(n) {
  const ids = baseCards.map((c) => c.id);
  for (let i = ids.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ids[i], ids[j]] = [ids[j], ids[i]];
  }
  return ids.slice(0, n).map((card_id) => ({ card_id, is_reversed: Math.random() < 0.3 }));
}

function handle(method, path, body) {
  const [pathname, qs] = path.split("?");
  const params = new URLSearchParams(qs);
  const seg = pathname.split("/").filter(Boolean);
  const route = `${method} /${seg.map((s) => (/^\d+$/.test(s) ? ":id" : s)).join("/")}`;
  const id = seg.find((s) => /^\d+$/.test(s));

  switch (route) {
    case "POST /auth/login":
      return { access_token: "mock-token", token_type: "bearer", user: USER };
    case "POST /auth/register":
      return USER;
    case "GET /auth/me":
      return USER;
    case "GET /spreads":
      return spreads;
    case "GET /me/quota":
      return quota();
    case "GET /readings": {
      const limit = Number(params.get("limit") ?? 20);
      const offset = Number(params.get("offset") ?? 0);
      return [...db.readings].reverse().slice(offset, offset + limit).map(toResponse);
    }
    case "POST /readings": {
      const spread = spreads[body.spread_id - 1] ?? fail(404, "Kiểu trải bài không tồn tại.");
      const question = String(body.question ?? "").trim();
      if (!question) fail(422, "Câu hỏi không được để trống.");
      if (question.length > 300) fail(422, "Câu hỏi tối đa 300 ký tự.");
      const r = {
        id: db.nextId++,
        spread_id: spread.id,
        question,
        created_at: new Date().toISOString(),
        ai_status: "done",
        ai_interpretation: null,
        cards: drawCards(spread.card_count),
      };
      r.ai_interpretation = interpret(db, r);
      db.readings.push(r);
      save();
      return toResponse(r);
    }
    case "GET /readings/:id":
      return toResponse(findReading(id));
    case "DELETE /readings/:id":
      findReading(id);
      db.readings = db.readings.filter((r) => r.id !== Number(id));
      save();
      return null;
    case "POST /readings/:id/interpret": {
      const r = findReading(id);
      if (r.ai_status !== "done") {
        r.ai_status = "done";
        r.ai_interpretation = interpret(db, r);
        save();
      }
      return toResponse(r);
    }
    case "GET /cards": {
      const limit = Number(params.get("limit") ?? 12);
      const offset = Number(params.get("offset") ?? 0);
      return baseCards.slice(offset, offset + limit).map((c) => card(db, c.id));
    }
    case "GET /admin/cards":
      return baseCards.map((c) => card(db, c.id));
    case "PUT /admin/cards/:id": {
      if (!baseCards[id - 1]) fail(404, "Không tìm thấy lá bài.");
      const up = String(body.upright_meaning ?? "").trim();
      const rev = String(body.reversed_meaning ?? "").trim();
      if (!up || !rev) fail(422, "Ý nghĩa không được để trống.");
      if (up.length > 1000 || rev.length > 1000) fail(422, "Ý nghĩa tối đa 1000 ký tự.");
      db.cardEdits[id] = { upright_meaning: up, reversed_meaning: rev };
      save();
      return card(db, Number(id));
    }
    default:
      return fail(404, `Mock chưa hỗ trợ ${method} ${pathname}`);
  }
}

// Giả lập độ trễ mạng để thấy trạng thái đang tải; bốc bài lâu hơn như đang chờ AI
export async function mockRequest(path, { method = "GET", body } = {}) {
  await new Promise((r) => setTimeout(r, method === "POST" && path === "/readings" ? 1500 : 300));
  return structuredClone(handle(method, path, body));
}
