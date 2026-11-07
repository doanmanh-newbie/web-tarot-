from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends

from app.config import get_settings
from app.modules.auth.domain.user import Role, User
from app.modules.auth.presentation.dependencies import get_current_user, require_admin


# ------------------------------------------------------------------ đăng ký
def test_register_success(ctx):
    res = ctx.client.post("/auth/register", json={"email": "A@Example.com", "password": "matkhau123"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_returns_409_without_leaking_email(ctx):
    ctx.client.post("/auth/register", json={"email": "a@example.com", "password": "matkhau123"})
    res = ctx.client.post("/auth/register", json={"email": "A@example.com", "password": "matkhau456"})
    assert res.status_code == 409
    assert "a@example.com" not in res.text


def test_register_ignores_attempt_to_set_admin_role(ctx):
    res = ctx.client.post(
        "/auth/register", json={"email": "a@example.com", "password": "matkhau123", "role": "admin"}
    )
    assert res.status_code == 422


def test_register_validation_errors(ctx):
    bad_email = {"email": "khong-phai-email", "password": "matkhau123"}
    assert ctx.client.post("/auth/register", json=bad_email).status_code == 422
    assert ctx.client.post("/auth/register", json={"email": "a@example.com", "password": "ngan"}).status_code == 422
    assert ctx.client.post("/auth/register", json={"email": "a@example.com"}).status_code == 422


def test_register_password_over_72_bytes_returns_422(ctx):
    res = ctx.client.post("/auth/register", json={"email": "a@example.com", "password": "ệ" * 40})
    assert res.status_code == 422


# ------------------------------------------------------------------ đăng nhập
def test_login_success_returns_token_and_user(ctx):
    ctx.make_user("a@example.com")
    res = ctx.client.post("/auth/login", json={"email": "a@example.com", "password": "matkhau123"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "a@example.com"


def test_login_wrong_password_and_unknown_email_look_identical(ctx):
    ctx.make_user("a@example.com")
    wrong_pw = ctx.client.post("/auth/login", json={"email": "a@example.com", "password": "sai-mat-khau"})
    unknown = ctx.client.post("/auth/login", json={"email": "khong@example.com", "password": "matkhau123"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()
    assert wrong_pw.headers["www-authenticate"] == "Bearer"


# ------------------------------------------------------------------ xác thực token
def test_me_with_valid_token(ctx):
    ctx.make_user("a@example.com")
    token = ctx.login("a@example.com")
    res = ctx.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "a@example.com"


def test_me_without_token_is_401(ctx):
    res = ctx.client.get("/auth/me")
    assert res.status_code == 401
    assert res.headers["www-authenticate"] == "Bearer"


def test_me_with_garbage_token_is_401(ctx):
    assert ctx.client.get("/auth/me", headers={"Authorization": "Bearer rac-roi"}).status_code == 401


def test_me_with_expired_token_is_401(ctx):
    ctx.make_user("a@example.com")
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {"sub": "1", "role": "user", "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)},
        get_settings().jwt_secret,
        algorithm="HS256",
    )
    assert ctx.client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_token_of_deleted_user_is_401(ctx):
    ctx.make_user("a@example.com")
    token = ctx.login("a@example.com")
    from app.modules.auth.infrastructure.models import UserModel

    with ctx.session_factory() as session:
        session.query(UserModel).delete()
        session.commit()
    assert ctx.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# ------------------------------------------------------------------ phân quyền
def _add_protected_routes(app):
    @app.get("/_test/user")
    def user_only(user: User = Depends(get_current_user)):
        return {"id": user.id}

    @app.get("/_test/admin")
    def admin_only(user: User = Depends(require_admin)):
        return {"id": user.id}


def test_admin_route_forbidden_for_normal_user(ctx):
    _add_protected_routes(ctx.app)
    ctx.make_user("user@example.com")
    token = ctx.login("user@example.com")
    res = ctx.client.get("/_test/admin", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_admin_route_allows_admin(ctx):
    _add_protected_routes(ctx.app)
    ctx.make_user("admin@example.com", role=Role.ADMIN)
    token = ctx.login("admin@example.com")
    res = ctx.client.get("/_test/admin", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_admin_route_requires_login(ctx):
    _add_protected_routes(ctx.app)
    assert ctx.client.get("/_test/admin").status_code == 401


def test_role_change_takes_effect_immediately_with_old_token(ctx):
    _add_protected_routes(ctx.app)
    ctx.make_user("user@example.com")
    token = ctx.login("user@example.com")
    from app.modules.auth.infrastructure.models import UserModel

    with ctx.session_factory() as session:
        session.query(UserModel).update({"role": "admin"})
        session.commit()
    res = ctx.client.get("/_test/admin", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
