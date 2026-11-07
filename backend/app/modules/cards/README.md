# Module `cards`

Bộ bài 78 lá (22 Major + 4 bộ x 14 Minor) và phần admin chỉnh ý nghĩa.

Phụ thuộc module khác: không (router dùng `auth.presentation.dependencies.require_admin`).
Module `readings` dùng `CardRepository.get_by_ids()` để lấy ý nghĩa gốc của các lá vừa bốc rồi đưa vào prompt cho AI.

## Endpoint (chỉ admin)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/admin/cards` | Toàn bộ 78 lá |
| GET | `/admin/cards/{id}` | Một lá |
| PUT | `/admin/cards/{id}` | Sửa ý nghĩa xuôi/ngược (chỉ hai field này) |

## Dữ liệu

- Nguồn: `scripts/data/cards.json` (nội dung ý nghĩa viết lại bằng lời của nhóm, không chép từ sách/website).
- `slug` là khóa tự nhiên (`the-fool`, `ace-of-wands`), dùng để seed upsert.
- `number`: Major 0-21; Minor 1-14 (Ace=1, Page=11, Knight=12, Queen=13, King=14).
- `image_url` có dạng `/cards/<slug>.jpg`. File ảnh do frontend đặt ở `frontend/public/cards/`
  (xem `frontend/public/cards/README.md` về nguồn ảnh và bản quyền).

## Quyết định thiết kế

| Vấn đề | Cách xử lý |
|---|---|
| Admin sửa được gì | Chỉ ý nghĩa xuôi/ngược; schema `extra=forbid` nên không đổi được tên, loại, số lá |
| Nội dung rỗng | Luật ở `domain/meaning_policy.py` (không rỗng, tối đa 1000 ký tự) |
| Seed chạy lại | Mặc định không ghi đè, để không mất chỉnh sửa của admin; `--update` mới ghi đè |
