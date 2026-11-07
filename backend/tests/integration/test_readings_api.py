from datetime import datetime, timezone

from app.modules.auth.domain.user import Role

ONE, THREE, FIVE = 1, 2, 3  # id kiểu trải bài sau khi seed


def draw(ctx, headers, spread_id=THREE, question="Công việc sắp tới thế nào?"):
    return ctx.client.post("/readings", json={"spread_id": spread_id, "question": question}, headers=headers)


def quota(ctx, headers):
    return ctx.client.get("/me/quota", headers=headers).json()


# ---------------------------------------------------------------- bốc bài
def test_draw_requires_login(ctx):
    ctx.seed()
    assert ctx.client.post("/readings", json={"spread_id": 1, "question": "q"}).status_code == 401


def test_draw_returns_cards_positions_and_interpretation(ctx):
    ctx.seed()
    res = draw(ctx, ctx.auth_header())
    assert res.status_code == 201
    body = res.json()
    assert body["spread"]["name"].startswith("Quá khứ")
    assert body["ai_status"] == "done" and body["ai_interpretation"] == "Lời diễn giải thử nghiệm"
    assert [c["position_label"] for c in body["cards"]] == ["Quá khứ", "Hiện tại", "Tương lai"]
    assert [c["position_index"] for c in body["cards"]] == [0, 1, 2]
    first = body["cards"][0]
    assert {"id", "slug", "name", "name_vi", "image_url"} <= first["card"].keys()
    assert isinstance(first["is_reversed"], bool) and first["meaning"]
    assert "giải trí" in body["disclaimer"]


def test_drawn_cards_are_distinct_and_meaning_matches_orientation(ctx):
    ctx.seed()
    headers = ctx.auth_header(Role.ADMIN)  # admin không bị giới hạn nên bốc nhiều lần được
    admin_cards = {c["id"]: c for c in ctx.client.get("/admin/cards", headers=headers).json()}
    for _ in range(15):
        cards = draw(ctx, headers, FIVE).json()["cards"]
        ids = [c["card"]["id"] for c in cards]
        assert len(set(ids)) == 5
        for c in cards:
            source = admin_cards[c["card"]["id"]]
            expected = source["reversed_meaning"] if c["is_reversed"] else source["upright_meaning"]
            assert c["meaning"] == expected


def test_ai_receives_the_cards_that_were_drawn(ctx):
    ctx.seed()
    body = draw(ctx, ctx.auth_header()).json()
    sent = ctx.ai.calls[0]
    assert [c.is_reversed for c in sent.cards] == [c["is_reversed"] for c in body["cards"]]
    assert [c.base_meaning for c in sent.cards] == [c["meaning"] for c in body["cards"]]


def test_unknown_spread_is_404_and_free(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    assert draw(ctx, headers, spread_id=999).status_code == 404
    assert quota(ctx, headers)["used"] == 0


def test_invalid_questions_are_rejected_and_free(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    blank = draw(ctx, headers, question="    ")
    assert blank.status_code == 422 and "câu hỏi" in blank.json()["detail"].lower()
    assert draw(ctx, headers, question="x" * 301).status_code == 422
    extra = ctx.client.post("/readings", json={"spread_id": 1, "question": "q", "user_id": 99}, headers=headers)
    assert extra.status_code == 422
    assert quota(ctx, headers)["used"] == 0


def test_unseeded_database_is_404_not_500(ctx):
    assert draw(ctx, ctx.auth_header()).status_code == 404


# ---------------------------------------------------------------- quota
def test_quota_endpoint_requires_login(ctx):
    assert ctx.client.get("/me/quota").status_code == 401


def test_initial_quota(ctx):
    q = quota(ctx, ctx.auth_header())
    assert (q["limit"], q["used"], q["remaining"], q["unlimited"]) == (3, 0, 3, False)
    assert q["resets_at"].endswith("+07:00")


def test_fourth_draw_is_blocked_with_429(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    for expected_remaining in (2, 1, 0):
        assert draw(ctx, headers, ONE).status_code == 201
        assert quota(ctx, headers)["remaining"] == expected_remaining
    blocked = draw(ctx, headers, ONE)
    assert blocked.status_code == 429 and "hết lượt" in blocked.json()["detail"]
    assert len(ctx.ai.calls) == 3  # lần bị chặn không tốn lượt gọi Gemini


def test_quota_is_per_user(ctx):
    ctx.seed()
    a = ctx.auth_header(email="a@example.com")
    b = ctx.auth_header(email="b@example.com")
    for _ in range(3):
        draw(ctx, a, ONE)
    assert draw(ctx, a, ONE).status_code == 429
    assert draw(ctx, b, ONE).status_code == 201


def test_admin_is_unlimited(ctx):
    ctx.seed()
    headers = ctx.auth_header(Role.ADMIN)
    for _ in range(5):
        assert draw(ctx, headers, ONE).status_code == 201
    q = quota(ctx, headers)
    assert (q["unlimited"], q["limit"], q["remaining"], q["used"]) == (True, None, None, 5)


def test_quota_resets_at_midnight_vietnam_time(ctx):
    ctx.seed()
    headers = ctx.auth_header()  # đăng nhập trước khi chỉnh đồng hồ
    ctx.clock.at = datetime(2026, 1, 15, 16, 59, tzinfo=timezone.utc)  # 23:59 giờ VN
    for _ in range(3):
        assert draw(ctx, headers, ONE).status_code == 201
    assert draw(ctx, headers, ONE).status_code == 429
    assert quota(ctx, headers)["resets_at"] == "2026-01-16T00:00:00+07:00"
    ctx.clock.at = datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)  # 00:00 giờ VN ngày mới
    assert quota(ctx, headers)["remaining"] == 3
    assert draw(ctx, headers, ONE).status_code == 201


# ---------------------------------------------------------------- AI lỗi và giải lại
def test_ai_failure_keeps_reading_counts_draw_and_can_be_retried(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    ctx.ai.fail = True
    res = draw(ctx, headers)
    assert res.status_code == 201  # bài vẫn được lưu
    body = res.json()
    assert body["ai_status"] == "failed" and body["ai_interpretation"] is None and len(body["cards"]) == 3
    assert quota(ctx, headers)["used"] == 1

    ctx.ai.fail = False
    retry = ctx.client.post(f"/readings/{body['id']}/interpret", headers=headers)
    assert retry.status_code == 200
    again = retry.json()
    assert again["ai_status"] == "done" and again["ai_interpretation"]
    assert [c["card"]["id"] for c in again["cards"]] == [c["card"]["id"] for c in body["cards"]]  # cùng lá bài
    assert quota(ctx, headers)["used"] == 1  # giải lại không tốn lượt


def test_retry_of_done_reading_does_not_call_ai_again(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    rid = draw(ctx, headers).json()["id"]
    calls = len(ctx.ai.calls)
    assert ctx.client.post(f"/readings/{rid}/interpret", headers=headers).status_code == 200
    assert len(ctx.ai.calls) == calls


def test_retry_that_fails_again_still_returns_200_with_failed_status(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    ctx.ai.fail = True
    rid = draw(ctx, headers).json()["id"]
    res = ctx.client.post(f"/readings/{rid}/interpret", headers=headers)
    assert res.status_code == 200 and res.json()["ai_status"] == "failed"


# ---------------------------------------------------------------- lịch sử
def test_history_lists_only_my_readings_newest_first(ctx):
    ctx.seed()
    a = ctx.auth_header(email="a@example.com")
    b = ctx.auth_header(email="b@example.com")
    first = draw(ctx, a, ONE, "câu một").json()["id"]
    second = draw(ctx, a, ONE, "câu hai").json()["id"]
    draw(ctx, b, ONE, "của b")
    history = ctx.client.get("/readings", headers=a).json()
    assert [r["id"] for r in history] == [second, first]
    assert [r["question"] for r in history] == ["câu hai", "câu một"]
    assert len(ctx.client.get("/readings?limit=1", headers=a).json()) == 1
    assert len(ctx.client.get("/readings?limit=1&offset=1", headers=a).json()) == 1
    assert ctx.client.get("/readings?limit=0", headers=a).status_code == 422


def test_history_requires_login(ctx):
    assert ctx.client.get("/readings").status_code == 401


def test_get_one_reading(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    rid = draw(ctx, headers).json()["id"]
    res = ctx.client.get(f"/readings/{rid}", headers=headers)
    assert res.status_code == 200 and res.json()["id"] == rid and len(res.json()["cards"]) == 3


def test_other_users_cannot_see_interpret_or_delete_my_reading(ctx):
    ctx.seed()
    owner = ctx.auth_header(email="owner@example.com")
    intruder = ctx.auth_header(email="intruder@example.com")
    rid = draw(ctx, owner).json()["id"]
    assert ctx.client.get(f"/readings/{rid}", headers=intruder).status_code == 404
    assert ctx.client.post(f"/readings/{rid}/interpret", headers=intruder).status_code == 404
    assert ctx.client.delete(f"/readings/{rid}", headers=intruder).status_code == 404
    assert ctx.client.get(f"/readings/{rid}", headers=owner).status_code == 200  # vẫn còn nguyên


def test_delete_removes_from_history_but_keeps_quota_used(ctx):
    ctx.seed()
    headers = ctx.auth_header()
    ids = [draw(ctx, headers, ONE).json()["id"] for _ in range(3)]
    assert ctx.client.delete(f"/readings/{ids[0]}", headers=headers).status_code == 204
    assert ctx.client.get(f"/readings/{ids[0]}", headers=headers).status_code == 404
    assert [r["id"] for r in ctx.client.get("/readings", headers=headers).json()] == [ids[2], ids[1]]
    assert quota(ctx, headers)["used"] == 3  # xóa lịch sử không hoàn lượt
    assert draw(ctx, headers, ONE).status_code == 429
    assert ctx.client.delete(f"/readings/{ids[0]}", headers=headers).status_code == 404  # xóa lần hai


def test_unknown_reading_is_404(ctx):
    headers = ctx.auth_header()
    assert ctx.client.get("/readings/999", headers=headers).status_code == 404
