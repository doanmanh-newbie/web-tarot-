import pytest

from app.modules.auth.application.use_cases.login_user import LoginUser
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import InvalidCredentials
from tests.unit.modules.auth.fakes import FakeHasher, FakeTokenService, FakeUserRepository


@pytest.fixture
def ctx():
    repo, hasher = FakeUserRepository(), FakeHasher()
    RegisterUser(repo, hasher).execute("a@example.com", "matkhau123")
    hasher.verify_calls = 0
    return LoginUser(repo, hasher, FakeTokenService(), dummy_hash="hashed:dummy"), hasher


def test_login_success_returns_token_and_user(ctx):
    login, _ = ctx
    result = login.execute("a@example.com", "matkhau123")
    assert result.access_token == "token:1:user"
    assert result.user.email == "a@example.com"


def test_login_email_is_case_insensitive(ctx):
    login, _ = ctx
    assert login.execute("  A@Example.com ", "matkhau123").user.id == 1


def test_wrong_password_raises_invalid_credentials(ctx):
    login, _ = ctx
    with pytest.raises(InvalidCredentials):
        login.execute("a@example.com", "sai-mat-khau")


def test_unknown_email_raises_same_error(ctx):
    login, _ = ctx
    with pytest.raises(InvalidCredentials):
        login.execute("khong-ton-tai@example.com", "matkhau123")


def test_unknown_email_still_runs_a_password_verification(ctx):
    # chống dò email qua thời gian phản hồi
    login, hasher = ctx
    with pytest.raises(InvalidCredentials):
        login.execute("khong-ton-tai@example.com", "matkhau123")
    assert hasher.verify_calls == 1
