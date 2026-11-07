from app.modules.auth.domain.user import Role


def test_list_requires_login(ctx):
    assert ctx.client.get("/spreads").status_code == 401


def test_user_lists_spreads_with_ordered_positions(ctx):
    ctx.seed()
    res = ctx.client.get("/spreads", headers=ctx.auth_header(Role.USER))
    assert res.status_code == 200
    spreads = res.json()
    assert [s["card_count"] for s in spreads] == [1, 3, 5]
    three = spreads[1]
    assert three["name"].startswith("Quá khứ")
    assert [p["label"] for p in three["positions"]] == ["Quá khứ", "Hiện tại", "Tương lai"]
    assert [p["index"] for p in three["positions"]] == [0, 1, 2]


def test_get_one_spread(ctx):
    ctx.seed()
    res = ctx.client.get("/spreads/2", headers=ctx.auth_header(Role.USER))
    assert res.status_code == 200 and res.json()["slug"] == "past-present-future"


def test_get_unknown_spread_is_404(ctx):
    ctx.seed()
    assert ctx.client.get("/spreads/99", headers=ctx.auth_header(Role.USER)).status_code == 404
