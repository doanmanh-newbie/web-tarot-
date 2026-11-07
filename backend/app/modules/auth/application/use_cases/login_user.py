from dataclasses import dataclass

from app.modules.auth.application.ports.password_hasher import PasswordHasher
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.exceptions import InvalidCredentials
from app.modules.auth.domain.user import User
from app.modules.auth.domain.user_repository import UserRepository


@dataclass
class LoginResult:
    access_token: str
    user: User


class LoginUser:
    """Đăng nhập, trả JWT.

    - Sai email và sai mật khẩu cho CÙNG một lỗi (InvalidCredentials), tránh lộ email nào đã đăng ký.
    - Email không tồn tại vẫn chạy một lần verify với `dummy_hash` để thời gian phản hồi
      không khác so với trường hợp sai mật khẩu (chống dò email bằng thời gian).
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        dummy_hash: str,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._dummy_hash = dummy_hash

    def execute(self, email: str, password: str) -> LoginResult:
        user = self._users.get_by_email(email.strip().lower())
        if user is None:
            self._hasher.verify(password, self._dummy_hash)
            raise InvalidCredentials()
        if not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentials()
        token = self._tokens.create_access_token(user.id, user.role.value)
        return LoginResult(access_token=token, user=user)
