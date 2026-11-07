from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.exceptions import InvalidToken
from app.modules.auth.domain.user import User
from app.modules.auth.domain.user_repository import UserRepository


class AuthenticateToken:
    """Từ JWT tìm ra User hiện tại.

    Luôn đọc lại user từ DB: user đã bị xóa thì token coi như vô hiệu, và quyền (role)
    lấy từ DB chứ không tin claim trong token (đổi quyền có hiệu lực ngay).
    """

    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    def execute(self, token: str) -> User:
        payload = self._tokens.decode(token)
        try:
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidToken("Token không hợp lệ") from exc
        user = self._users.get_by_id(user_id)
        if user is None:
            raise InvalidToken("Tài khoản không còn tồn tại")
        return user
