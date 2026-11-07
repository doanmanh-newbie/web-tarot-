"""Bản giả (in-memory) của repository/port để test use case không cần DB hay bcrypt thật."""
from dataclasses import replace

from app.modules.auth.application.ports.password_hasher import PasswordHasher
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.exceptions import EmailAlreadyUsed, InvalidToken
from app.modules.auth.domain.user import User
from app.modules.auth.domain.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self._next_id = 1

    def get_by_id(self, user_id):
        return self.users.get(user_id)

    def get_by_email(self, email):
        return next((u for u in self.users.values() if u.email == email), None)

    def add(self, user):
        if self.get_by_email(user.email):
            raise EmailAlreadyUsed(user.email)
        saved = replace(user, id=self._next_id)
        self.users[saved.id] = saved
        self._next_id += 1
        return saved


class FakeHasher(PasswordHasher):
    def __init__(self) -> None:
        self.verify_calls = 0

    def hash(self, plain):
        return f"hashed:{plain}"

    def verify(self, plain, hashed):
        self.verify_calls += 1
        return hashed == f"hashed:{plain}"


class FakeTokenService(TokenService):
    def create_access_token(self, user_id, role):
        return f"token:{user_id}:{role}"

    def decode(self, token):
        if not token.startswith("token:"):
            raise InvalidToken("bad")
        _, uid, role = token.split(":")
        return {"sub": uid, "role": role}
