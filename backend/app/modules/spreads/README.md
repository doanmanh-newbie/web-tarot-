# Module `spreads`

Các kiểu trải bài và nhãn/mô tả từng vị trí.

Phụ thuộc module khác: không (router dùng `auth.presentation.dependencies.get_current_user`).
Module `readings` dùng `SpreadRepository.get_by_id()` để biết cần bốc mấy lá và nhãn từng vị trí.

## Endpoint (cần đăng nhập)

| Method | Path | Mô tả |
|---|---|---|
| GET | `/spreads` | Danh sách kiểu trải bài kèm vị trí |
| GET | `/spreads/{id}` | Một kiểu trải bài |

## Dữ liệu (`scripts/data/spreads.json`)

| slug | Số lá | Vị trí |
|---|---|---|
| `one-card` | 1 | Thông điệp |
| `past-present-future` | 3 | Quá khứ, Hiện tại, Tương lai |
| `five-card-situation` | 5 | Hiện tại, Thách thức, Gốc rễ, Lời khuyên, Kết quả tiềm năng |

- Số lá của một kiểu = số vị trí của nó (`card_count` suy ra từ `positions`, không lưu riêng, không thể lệch).
- `position_index` bắt đầu từ 0. Mỗi vị trí có `description` để đưa vào prompt cho AI.
- Thêm kiểu trải bài mới: thêm một mục vào `spreads.json` rồi chạy `python -m scripts.seed_cards`.
