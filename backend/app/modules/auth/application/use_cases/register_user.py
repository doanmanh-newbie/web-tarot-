from app.modules.auth.application.ports.password_hasher import PasswordHasher
from app.modules.auth.domain.exceptions import EmailAlreadyUsed
from app.modules.auth.domain.password_policy import validate_password
from app.modules.auth.domain.user import Role, User
from app.modules.auth.domain.user_repository import UserRepository


class RegisterUser:
    """Đăng ký tài khoản.

    `role` chỉ dành cho script tạo admin. Router KHÔNG bao giờ truyền role từ request
    (người dùng tự đăng ký luôn là USER).
    """

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    def execute(self, email: str, password: str, role: Role = Role.USER) -> User:
        email = email.strip().lower()
        validate_password(password)
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyUsed(email)
        user = User(id=None, email=email, password_hash=self._hasher.hash(password), role=role)
        # Nếu hai request cùng lọt qua bước kiểm tra trên, ràng buộc UNIQUE trong DB
        # sẽ chặn và repository raise EmailAlreadyUsed.
        return self._users.add(user)
