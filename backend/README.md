# Backend - FastAPI, Clean Architecture chia theo module

## Tạo môi trường ảo (venv)

```bash
cd backend
python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements-dev.txt
```

Thoát venv: `deactivate`. `.venv/` đã nằm trong `.gitignore`, không commit.
Thêm thư viện: `pip install <tên>` rồi ghi vào `requirements.txt` (hoặc `requirements-dev.txt` nếu chỉ dùng để dev/test).

## Chạy

```bash
cp .env.example .env              # điền GEMINI_API_KEY, JWT_SECRET (chưa có key: đặt AI_PROVIDER=offline)
alembic upgrade head              # tạo bảng
python -m scripts.seed_cards      # nạp 78 lá bài + 3 kiểu trải bài (idempotent, không ghi đè chỉnh sửa của admin)
python -m scripts.create_admin admin@example.com   # tạo admin (hỏi mật khẩu qua prompt)
uvicorn app.main:app --reload     # Swagger: http://localhost:8000/docs
pytest                            # chạy test (gồm test kiểm tra kiến trúc)
# test chống lách lượt khi bấm đồng thời cần PostgreSQL thật (không có thì tự bỏ qua):
TEST_POSTGRES_URL=postgresql+psycopg://tarot:tarot@localhost:5432/tarot_test pytest tests/integration
ruff check .                      # lint
```

Migration: `alembic revision --autogenerate -m "mô tả"` rồi `alembic upgrade head`.

## Cấu trúc

```
app/
├── main.py            tạo FastAPI app
├── config.py          đọc biến môi trường
├── api_router.py      gom router của các module
├── error_handlers.py  map lỗi nghiệp vụ -> mã HTTP
├── shared/            thứ dùng chung (DomainError, Clock, DB session)
└── modules/
    ├── auth/          đăng ký, đăng nhập, JWT, phân quyền
    ├── cards/         bộ bài 78 lá (+ admin sửa ý nghĩa)
    ├── spreads/       các kiểu trải bài
    ├── quota/         luật giới hạn lượt bốc mỗi ngày
    └── readings/      bốc bài, diễn giải AI, lịch sử
```

Mỗi module có 4 tầng:

```
<module>/
├── domain/           entity, interface repository, exception, luật thuần
├── application/      use_cases/ + ports/ (interface ra thế giới ngoài)
├── infrastructure/   SQLAlchemy model + repository, Gemini, bcrypt, JWT...
└── presentation/     router, schemas, dependencies.py
```

## Quy tắc

**Trong một module** (phụ thuộc chỉ đi vào trong):

```
presentation ──► application ──► domain
infrastructure ─► application ──► domain
```

- `domain`: không import FastAPI, SQLAlchemy, pydantic, Gemini, bcrypt, JWT.
- `application`: không import FastAPI, SQLAlchemy, Gemini... Chỉ làm việc qua port.
- `presentation/dependencies.py` là nơi lắp ráp (composition root) của module: được phép import
  `infrastructure` của chính module để gắn implementation vào use case.

**Giữa các module:**

| Module | Được phụ thuộc |
|---|---|
| `auth`, `cards`, `spreads`, `quota` | không module nào (chỉ `shared`) |
| `readings` | `quota`, `cards`, `spreads` |

- Module A chỉ được import `domain` và `application` của module B, không import `infrastructure`/`presentation` của B.
- Ngoại lệ: các file `dependencies.py` (lắp ráp) được import implementation. Tầng `presentation` (chỉ `router.py`,
  `dependencies.py`) của module khác được dùng `auth.presentation.dependencies` (`get_current_user`, `require_admin`)
  và `auth.domain` (`User`, `Role`) để biết ai đang đăng nhập.
- Module `quota` không có tầng presentation: `GET /me/quota` nằm trong router của `readings` (xem `quota/README.md`).
- Không để phụ thuộc vòng. `shared` không được import module nào.

Các quy tắc trên được kiểm tra tự động bởi `tests/architecture/test_dependency_rules.py`.
Vi phạm thì CI đỏ.

## Thêm một module mới

1. Tạo `app/modules/<tên>/` với 4 tầng như trên.
2. Khai báo model trong `infrastructure/models.py`, rồi import vào `alembic/env.py`.
3. Tạo `router` trong `presentation/router.py`, thêm vào `app/api_router.py`.
4. Map lỗi của module trong `app/error_handlers.py`.
5. Nếu module phụ thuộc module khác, cập nhật bảng `ALLOWED_DEPENDENCIES` trong test kiến trúc và bảng trên.

## Luồng bốc bài (ví dụ)

`POST /readings` → `readings.presentation.router` → use case `DrawReading`:
kiểm tra quota (`quota.domain`) → lấy bài/kiểu trải (`cards`, `spreads`) → `RandomSource` bốc bài
→ `ReadingRepository` lưu → `AIInterpreter` (Gemini) diễn giải → cập nhật kết quả.

## Test

- `tests/unit/modules/<module>/`: test domain + use case bằng repo/AI giả, không cần DB, không cần mạng.
- `tests/integration/`: test API qua `TestClient`.
- `tests/architecture/`: kiểm tra quy tắc phụ thuộc giữa các tầng và module.
