import pytest

from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.exceptions import EmailAlreadyUsed, WeakPassword
from app.modules.auth.domain.user import Role
from tests.unit.modules.auth.fakes import FakeHasher, FakeUserRepository


def make():
    repo = FakeUserRepository()
    return RegisterUser(repo, FakeHasher()), repo


def test_register_creates_user_with_hashed_password():
    use_case, repo = make()
    user = use_case.execute("a@example.com", "matkhau123")
    assert user.id is not None
    assert user.password_hash == "hashed:matkhau123"
    assert user.password_hash != "matkhau123"
    assert repo.get_by_email("a@example.com") is not None


def test_register_defaults_to_user_role():
    use_case, _ = make()
    assert use_case.execute("a@example.com", "matkhau123").role is Role.USER


def test_register_normalizes_email():
    use_case, _ = make()
    assert use_case.execute("  Mixed@Example.COM ", "matkhau123").email == "mixed@example.com"


def test_register_duplicate_email_is_rejected_case_insensitively():
    use_case, _ = make()
    use_case.execute("a@example.com", "matkhau123")
    with pytest.raises(EmailAlreadyUsed):
        use_case.execute("A@EXAMPLE.com", "matkhau456")


@pytest.mark.parametrize("password", ["short", "1234567", "        ", "x" * 73])
def test_register_rejects_weak_password(password):
    use_case, repo = make()
    with pytest.raises(WeakPassword):
        use_case.execute("a@example.com", password)
    assert repo.get_by_email("a@example.com") is None


def test_password_limit_counts_bytes_not_characters():
    use_case, _ = make()
    # 40 ký tự nhưng 80 byte (mỗi "ệ" 3 byte dùng dạng dựng sẵn) -> vượt giới hạn bcrypt
    with pytest.raises(WeakPassword):
        use_case.execute("a@example.com", "ệ" * 40)


def test_admin_role_only_when_explicitly_requested():
    use_case, _ = make()
    assert use_case.execute("admin@example.com", "matkhau123", role=Role.ADMIN).role is Role.ADMIN
