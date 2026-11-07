"""Lắp ráp module auth + dependency cho module khác dùng.

Module khác import:
  get_current_user  - đọc JWT từ header `Authorization: Bearer <token>`, trả User (401 nếu sai/hết hạn)
  require_admin     - như trên nhưng bắt buộc role admin (403 nếu không phải)
"""
from functools import lru_cache

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.modules.auth.application.ports.password_hasher import PasswordHasher
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.application.use_cases.authenticate_token import AuthenticateToken
from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import InvalidToken
from app.modules.auth.domain.user import Role, User
from app.modules.auth.domain.user_repository import UserRepository
from app.modules.auth.infrastructure.bcrypt_hasher import BcryptHasher
from app.modules.auth.infrastructure.jwt_service import JwtTokenService
from app.modules.auth.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.shared.domain.exceptions import NotAuthorized
from app.shared.presentation.dependencies import get_clock, get_db_session

# auto_error=False: tự raise InvalidToken để lỗi đi qua error handler chung (401 + WWW-Authenticate)
_bearer = HTTPBearer(auto_error=False)

_dummy_hashes: dict[int, str] = {}


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session)


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return BcryptHasher()


def get_token_service(clock=Depends(get_clock)) -> TokenService:
    settings = get_settings()
    return JwtTokenService(settings.jwt_secret, settings.jwt_expire_minutes, clock)


def get_dummy_hash(hasher: PasswordHasher = Depends(get_password_hasher)) -> str:
    """Hash giả để LoginUser verify khi email không tồn tại (cache theo hasher, chỉ tính một lần)."""
    key = id(hasher)
    if key not in _dummy_hashes:
        _dummy_hashes[key] = hasher.hash("dummy-password-for-timing")
    return _dummy_hashes[key]


def get_register_user(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> RegisterUser:
    return RegisterUser(users, hasher)


def get_login_user(
    users: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
    tokens: TokenService = Depends(get_token_service),
    dummy_hash: str = Depends(get_dummy_hash),
) -> LoginUser:
    return LoginUser(users, hasher, tokens, dummy_hash)


def get_authenticate_token(
    users: UserRepository = Depends(get_user_repository),
    tokens: TokenService = Depends(get_token_service),
) -> AuthenticateToken:
    return AuthenticateToken(users, tokens)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    authenticate: AuthenticateToken = Depends(get_authenticate_token),
) -> User:
    if credentials is None:
        raise InvalidToken("Thiếu token đăng nhập")
    return authenticate.execute(credentials.credentials)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role is not Role.ADMIN:
        raise NotAuthorized("Chỉ quản trị viên được thực hiện thao tác này")
    return user
