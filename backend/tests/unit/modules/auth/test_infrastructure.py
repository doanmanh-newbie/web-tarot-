from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.modules.auth.domain.exceptions import InvalidToken
from app.modules.auth.infrastructure.bcrypt_hasher import BcryptHasher
from app.modules.auth.infrastructure.jwt_service import JwtTokenService
from app.shared.application.ports.clock import Clock

SECRET = "test-secret-test-secret-test-secret-0123456789"


class FixedClock(Clock):
    def __init__(self, at: datetime) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def service(at=None, secret=SECRET, minutes=60):
    return JwtTokenService(secret, minutes, FixedClock(at or datetime.now(timezone.utc)))


def test_bcrypt_hash_and_verify():
    hasher = BcryptHasher(rounds=4)
    hashed = hasher.hash("matkhau123")
    assert hashed != "matkhau123"
    assert hasher.verify("matkhau123", hashed)
    assert not hasher.verify("sai", hashed)


def test_bcrypt_same_password_gives_different_hashes():
    hasher = BcryptHasher(rounds=4)
    assert hasher.hash("matkhau123") != hasher.hash("matkhau123")


def test_bcrypt_verify_with_broken_hash_is_false_not_crash():
    assert BcryptHasher(rounds=4).verify("x", "khong-phai-hash") is False


def test_jwt_roundtrip():
    svc = service()
    payload = svc.decode(svc.create_access_token(7, "admin"))
    assert payload["sub"] == "7" and payload["role"] == "admin"


def test_jwt_expired_token_is_rejected():
    old = datetime.now(timezone.utc) - timedelta(hours=3)
    token = service(at=old, minutes=60).create_access_token(1, "user")
    with pytest.raises(InvalidToken):
        service().decode(token)


def test_jwt_wrong_secret_is_rejected():
    token = service(secret="khac-secret-khac-secret-khac-secret-0123456").create_access_token(1, "user")
    with pytest.raises(InvalidToken):
        service().decode(token)


def test_jwt_tampered_token_is_rejected():
    token = service().create_access_token(1, "user")
    with pytest.raises(InvalidToken):
        service().decode(token[:-3] + "abc")


def test_jwt_alg_none_is_rejected():
    claims = {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    forged = jwt.encode(claims, key=None, algorithm="none")
    with pytest.raises(InvalidToken):
        service().decode(forged)


def test_jwt_without_exp_is_rejected():
    token = jwt.encode({"sub": "1"}, SECRET, algorithm="HS256")
    with pytest.raises(InvalidToken):
        service().decode(token)
