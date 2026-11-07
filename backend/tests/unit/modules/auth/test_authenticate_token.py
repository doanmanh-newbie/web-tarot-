import pytest

from app.modules.auth.application.use_cases.authenticate_token import AuthenticateToken
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import InvalidToken
from tests.unit.modules.auth.fakes import FakeHasher, FakeTokenService, FakeUserRepository


@pytest.fixture
def ctx():
    repo = FakeUserRepository()
    RegisterUser(repo, FakeHasher()).execute("a@example.com", "matkhau123")
    return AuthenticateToken(repo, FakeTokenService()), repo


def test_valid_token_returns_user(ctx):
    authenticate, _ = ctx
    assert authenticate.execute("token:1:user").email == "a@example.com"


def test_garbage_token_is_rejected(ctx):
    authenticate, _ = ctx
    with pytest.raises(InvalidToken):
        authenticate.execute("rac-roi")


def test_token_of_deleted_user_is_rejected(ctx):
    authenticate, repo = ctx
    del repo.users[1]
    with pytest.raises(InvalidToken):
        authenticate.execute("token:1:user")


def test_role_comes_from_db_not_from_token(ctx):
    authenticate, _ = ctx
    # token tự khai role admin nhưng DB nói user -> vẫn là user
    assert authenticate.execute("token:1:admin").role.value == "user"
