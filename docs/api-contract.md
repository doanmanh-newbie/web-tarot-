# Hợp đồng API

Chốt request/response mẫu ở đây TRƯỚC khi hai người code song song.
Swagger tự sinh tại `/docs` khi chạy backend.

| Method | Path | Mô tả | Auth |
|---|---|---|---|
| POST | /auth/register | Đăng ký | - |
| POST | /auth/login | Đăng nhập, trả JWT | - |
| GET | /spreads | Danh sách kiểu trải bài | user |
| POST | /readings | Bốc bài + gọi AI | user |
| POST | /readings/{id}/interpret | Diễn giải lại khi AI lỗi | user |
| GET | /readings | Lịch sử của tôi | user |
| GET | /readings/{id} | Chi tiết một lần bốc | user (chủ sở hữu) |
| DELETE | /readings/{id} | Xóa | user (chủ sở hữu) |
| GET | /me/quota | Số lượt còn lại hôm nay | user |
| GET | /admin/cards | Xem bộ bài | admin |
| PUT | /admin/cards/{id} | Sửa ý nghĩa lá bài | admin |


---

## Chi tiết: Auth (đã cài đặt)

Gửi token ở mọi endpoint cần đăng nhập: `Authorization: Bearer <access_token>`.
Lỗi luôn có dạng `{"detail": "thông báo tiếng Việt"}`.

### POST /auth/register
Request:
```json
{ "email": "nam@example.com", "password": "matkhau123" }
```
- Email được chuẩn hóa về chữ thường. Mật khẩu: tối thiểu 8 ký tự, tối đa 72 byte.
- Không nhận field nào khác (gửi thêm `role` sẽ bị 422). Người đăng ký luôn là `user`.

Response `201`:
```json
{ "id": 1, "email": "nam@example.com", "role": "user" }
```
Lỗi: `409` email đã tồn tại, `422` dữ liệu sai (email không hợp lệ, mật khẩu yếu/quá dài).

### POST /auth/login
Request:
```json
{ "email": "nam@example.com", "password": "matkhau123" }
```
Response `200`:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "nam@example.com", "role": "user" }
}
```
Lỗi: `401` sai email hoặc mật khẩu (cùng một thông báo cho cả hai trường hợp).
Token hết hạn sau `JWT_EXPIRE_MINUTES` phút (mặc định 60). Hết hạn thì đăng nhập lại.

### GET /auth/me
Header cần token. Response `200`: `{ "id": 1, "email": "nam@example.com", "role": "user" }`

### Mã lỗi chung cho mọi endpoint cần đăng nhập

| Mã | Khi nào | Frontend nên làm |
|---|---|---|
| 401 | Thiếu/sai/hết hạn token, hoặc tài khoản đã bị xóa | Xóa token, chuyển về trang đăng nhập |
| 403 | Đăng nhập rồi nhưng không đủ quyền (vd user gọi `/admin/...`) | Hiện thông báo "không có quyền" |


---

## Chi tiết: Spreads (đã cài đặt, cần đăng nhập)

### GET /spreads
Response `200`:
```json
[
  {
    "id": 2, "slug": "past-present-future", "name": "Quá khứ - Hiện tại - Tương lai",
    "description": "Nhìn một tình huống theo dòng thời gian.", "card_count": 3,
    "positions": [
      { "index": 0, "label": "Quá khứ", "description": "Điều đã ảnh hưởng đến tình huống hiện tại." },
      { "index": 1, "label": "Hiện tại", "description": "..." },
      { "index": 2, "label": "Tương lai", "description": "..." }
    ]
  }
]
```
`positions` đã sắp theo `index` (bắt đầu từ 0). `GET /spreads/{id}` trả một phần tử như trên; `404` nếu không có.

## Chi tiết: Cards (đã cài đặt, chỉ admin)

Card object:
```json
{
  "id": 1, "slug": "the-fool", "name": "The Fool", "name_vi": "Chàng Khờ",
  "arcana": "major", "suit": null, "number": 0,
  "upright_meaning": "...", "reversed_meaning": "...", "image_url": "/cards/the-fool.jpg"
}
```
- `GET /admin/cards` trả mảng 78 card (sắp theo id). `GET /admin/cards/{id}` trả một card, `404` nếu không có.
- `PUT /admin/cards/{id}` body `{ "upright_meaning": "...", "reversed_meaning": "..." }`. Không nhận field nào khác (`422`).
  Nội dung rỗng hoặc quá 1000 ký tự: `422`. User thường gọi: `403`.
- `arcana`: `major` | `minor`. `suit`: `wands` | `cups` | `swords` | `pentacles` | `null` (Major).
- `image_url` là đường dẫn tương đối, frontend tự ghép domain (file đặt ở `frontend/public/cards/`).


---

## Chi tiết: Readings và Quota (đã cài đặt, cần đăng nhập)

### Reading object
```json
{
  "id": 12,
  "spread": { "id": 2, "name": "Quá khứ - Hiện tại - Tương lai" },
  "question": "Công việc sắp tới thế nào?",
  "created_at": "2026-10-29T08:15:30.123456Z",
  "ai_status": "done",
  "ai_interpretation": "Lời diễn giải...",
  "cards": [
    {
      "position_index": 0, "position_label": "Quá khứ", "is_reversed": false,
      "meaning": "Ý nghĩa gốc đúng chiều xuôi/ngược của lá này",
      "card": { "id": 1, "slug": "the-fool", "name": "The Fool", "name_vi": "Chàng Khờ", "image_url": "/cards/the-fool.jpg" }
    }
  ],
  "disclaimer": "Nội dung chỉ mang tính giải trí và tham khảo, không thay thế lời khuyên của chuyên gia."
}
```
- `ai_status`: `"done"` | `"failed"` | `"pending"`. **Khi khác `"done"` thì `ai_interpretation` là `null`: hiện nút "Giải lại"** (gọi `POST /readings/{id}/interpret`).
- `cards` đã sắp theo `position_index`. Lá ngược (`is_reversed: true`) nên hiển thị xoay 180 độ.
- Luôn hiển thị `disclaimer` cùng kết quả.

### POST /readings
Request: `{ "spread_id": 2, "question": "Công việc sắp tới thế nào?" }`
Không nhận field nào khác. Server tự bốc bài.

| Mã | Khi nào |
|---|---|
| 201 | Thành công. **Kể cả khi AI lỗi**: bài đã lưu, `ai_status = "failed"` |
| 404 | `spread_id` không tồn tại (hoặc chưa seed dữ liệu) |
| 422 | Câu hỏi rỗng hoặc quá 300 ký tự (`detail` là thông báo tiếng Việt, hiện thẳng cho người dùng) |
| 429 | Hết lượt hôm nay. Lỗi 404/422 **không** trừ lượt |
| 503 | Bộ bài chưa nạp đủ |

Gọi có thể mất tới ~20 giây (chờ AI): hiển thị trạng thái đang tải. Nếu Render free vừa "ngủ dậy" còn lâu hơn.

### POST /readings/{id}/interpret
Không body. Dùng khi `ai_status != "done"`. Không bốc lại bài, không tốn lượt. Trả `200` + reading
(có thể vẫn `"failed"` nếu AI tiếp tục lỗi). Reading đã `"done"` thì trả luôn kết quả cũ.

### GET /readings?limit=20&offset=0
Mảng reading của chính mình, mới nhất trước (`limit` 1..100). Không gồm reading đã xóa.

### GET /readings/{id}, DELETE /readings/{id}
`GET` trả reading; `DELETE` trả `204`. Reading của người khác hoặc không tồn tại: `404`.
**Xóa không hoàn lại lượt** (hãy nói rõ cho người dùng trong giao diện).

### GET /me/quota
```json
{ "limit": 3, "used": 1, "remaining": 2, "resets_at": "2026-10-30T00:00:00+07:00", "unlimited": false }
```
Admin: `{ "limit": null, "used": 5, "remaining": null, "unlimited": true, ... }`.
`resets_at` là 00:00 ngày mai giờ Việt Nam (hiển thị "làm mới lúc ..."). Nên gọi lại endpoint này sau mỗi lần bốc.
