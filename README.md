# Tarot Reading Web

Web xem bài Tarot có diễn giải bằng AI (Gemini). Đồ án môn Đồ án thực tế công nghệ phần mềm.

## Cấu trúc repo

```
tarot-web/
├── backend/     FastAPI + SQLAlchemy, Clean Architecture chia theo module
├── frontend/    React (Vite)
├── docs/        Thuyết minh, diagram, hợp đồng API, quy ước
├── .github/     CI + mẫu pull request
└── docker-compose.yml   Postgres chạy local
```

## Chạy nhanh (local)

```bash
# 1. Database
docker compose up -d db

# 2. Backend (xem backend/README.md để biết chi tiết venv)
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # rồi điền GEMINI_API_KEY, JWT_SECRET
alembic upgrade head
python -m scripts.seed_cards
uvicorn app.main:app --reload      # http://localhost:8000/docs

# 3. Frontend
cd ../frontend
cp .env.example .env
npm install
npm run dev                        # http://localhost:5173
```

## Quy ước làm việc

Xem `docs/CONVENTIONS.md`.
