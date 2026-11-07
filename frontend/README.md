# Frontend - React (Vite)

```bash
cp .env.example .env     # VITE_API_URL trỏ tới backend
npm install
npm run dev              # http://localhost:5173
npm run build
```

Gọi API qua `src/api/` (không `fetch` rải rác trong component).
Token JWT lưu trong `AuthContext`. Mọi call lỗi đều phải hiện thông báo cho người dùng.
