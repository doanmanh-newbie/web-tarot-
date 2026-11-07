# Module `auth`

Đăng ký, đăng nhập, phát/kiểm tra JWT, phân quyền user/admin.

Phụ thuộc module khác: không.
Cung cấp cho module khác: `presentation/dependencies.py` với `get_current_user` và `require_admin`.

## Endpoint

| Method | Path | Mô tả |
|---|---|---|
| POST | `/auth/register` | Đăng ký (luôn tạo role `user`) |
| POST | `/auth/login` | Đăng nhập, trả JWT + thông tin user |
| GET | `/auth/me` | Thông tin người đang đăng nhập (cần token) |

## Dùng ở router của module khác

```python
from app.modules.auth.presentation.dependencies import get_current_user, require_admin

@router.get("/readings")
def list_mine(user: User = Depends(get_current_user)): ...

@router.put("/{card_id}")
def update_card(..., admin: User = Depends(require_admin)): ...
```

## Quyết định thiết kế (đưa vào báo cáo)

| Vấn đề | Cách xử lý |
|---|---|
| Lưu mật khẩu | bcrypt (rounds 12), có salt riêng mỗi lần; không bao giờ lưu/trả mật khẩu thô |
| Mật khẩu dài hơn 72 byte | bcrypt cắt ở 72 byte nên chặn theo byte, tối thiểu 8 ký tự |
| Dò email đã đăng ký | Sai email và sai mật khẩu trả cùng một lỗi; email không tồn tại vẫn verify hash giả để thời gian phản hồi giống nhau |
| Đăng ký trùng email lúc đua | Ràng buộc UNIQUE trong DB là chốt chặn cuối, không chỉ kiểm tra trong code |
| JWT | HS256, bắt buộc có `exp`, chỉ chấp nhận đúng thuật toán (chặn `alg=none`), secret >= 32 ký tự ngoài môi trường dev |
| Quyền (role) | Lấy từ DB mỗi request, không tin claim trong token → đổi quyền/xóa user có hiệu lực ngay |
| Tự phong admin | Schema đăng ký `extra=forbid`; admin chỉ tạo bằng `python -m scripts.create_admin` |
| Mã lỗi | 401 chưa đăng nhập/token sai, 403 không đủ quyền, 409 trùng email, 422 dữ liệu sai |

## Chưa làm (ghi vào phần "hạn chế / hướng phát triển")

- Giới hạn số lần đăng nhập sai (rate limit chống brute-force)
- Refresh token / đăng xuất phía server (hiện token sống đến khi hết hạn; đăng xuất = frontend xóa token)
- Đổi mật khẩu, quên mật khẩu, xác thực email
