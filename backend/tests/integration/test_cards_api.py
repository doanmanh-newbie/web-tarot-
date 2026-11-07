from app.modules.auth.domain.user import Role


def test_list_requires_login(ctx):
    assert ctx.client.get("/admin/cards").status_code == 401


def test_list_forbidden_for_normal_user(ctx):
    ctx.seed()
    assert ctx.client.get("/admin/cards", headers=ctx.auth_header(Role.USER)).status_code == 403


def test_admin_lists_all_78_cards(ctx):
    ctx.seed()
    res = ctx.client.get("/admin/cards", headers=ctx.auth_header(Role.ADMIN))
    assert res.status_code == 200
    cards = res.json()
    assert len(cards) == 78
    assert cards[0]["name"] == "The Fool" and cards[0]["name_vi"] == "Chàng Khờ"
    assert {"upright_meaning", "reversed_meaning", "image_url", "arcana", "suit"} <= cards[0].keys()


def test_admin_gets_one_card(ctx):
    ctx.seed()
    res = ctx.client.get("/admin/cards/1", headers=ctx.auth_header(Role.ADMIN))
    assert res.status_code == 200 and res.json()["slug"] == "the-fool"


def test_get_unknown_card_is_404(ctx):
    ctx.seed()
    assert ctx.client.get("/admin/cards/999", headers=ctx.auth_header(Role.ADMIN)).status_code == 404


def test_admin_updates_meaning_and_it_persists(ctx):
    ctx.seed()
    headers = ctx.auth_header(Role.ADMIN)
    body = {"upright_meaning": "  Xuôi mới  ", "reversed_meaning": "Ngược mới"}
    res = ctx.client.put("/admin/cards/1", json=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["upright_meaning"] == "Xuôi mới"
    again = ctx.client.get("/admin/cards/1", headers=headers).json()
    assert again["reversed_meaning"] == "Ngược mới" and again["name"] == "The Fool"


def test_normal_user_cannot_update(ctx):
    ctx.seed()
    body = {"upright_meaning": "x", "reversed_meaning": "y"}
    assert ctx.client.put("/admin/cards/1", json=body, headers=ctx.auth_header(Role.USER)).status_code == 403


def test_update_rejects_blank_and_extra_fields(ctx):
    ctx.seed()
    headers = ctx.auth_header(Role.ADMIN)
    blank = {"upright_meaning": "   ", "reversed_meaning": "ok"}
    res = ctx.client.put("/admin/cards/1", json=blank, headers=headers)
    assert res.status_code == 422 and "không được để trống" in res.json()["detail"]
    extra = {"upright_meaning": "a", "reversed_meaning": "b", "name": "Hack"}
    assert ctx.client.put("/admin/cards/1", json=extra, headers=headers).status_code == 422
    assert ctx.client.get("/admin/cards/1", headers=headers).json()["name"] == "The Fool"


def test_update_unknown_card_is_404(ctx):
    ctx.seed()
    body = {"upright_meaning": "a", "reversed_meaning": "b"}
    res = ctx.client.put("/admin/cards/999", json=body, headers=ctx.auth_header(Role.ADMIN))
    assert res.status_code == 404
