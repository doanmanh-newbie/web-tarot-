from sqlalchemy import func, select

from app.modules.cards.infrastructure.models import CardModel
from app.modules.spreads.infrastructure.models import SpreadModel, SpreadPositionModel
from scripts.seed_cards import load_data, seed_database


def counts(ctx):
    with ctx.session_factory() as s:
        return (
            s.scalar(select(func.count()).select_from(CardModel)),
            s.scalar(select(func.count()).select_from(SpreadModel)),
            s.scalar(select(func.count()).select_from(SpreadPositionModel)),
        )


def test_seed_inserts_deck_and_spreads(ctx):
    report = ctx.seed()
    assert report.cards_added == 78 and report.spreads_added == 3
    assert counts(ctx) == (78, 3, 1 + 3 + 5)


def test_seed_is_idempotent(ctx):
    ctx.seed()
    report = ctx.seed()
    assert (report.cards_added, report.spreads_added) == (0, 0)
    assert report.cards_skipped == 78 and report.spreads_skipped == 3
    assert counts(ctx) == (78, 3, 9)


def test_seed_keeps_admin_edits_by_default(ctx):
    ctx.seed()
    with ctx.session_factory() as s:
        card = s.scalars(select(CardModel).where(CardModel.slug == "the-fool")).one()
        card.upright_meaning = "Admin đã sửa"
        s.commit()
    ctx.seed()
    with ctx.session_factory() as s:
        card = s.scalars(select(CardModel).where(CardModel.slug == "the-fool")).one()
        assert card.upright_meaning == "Admin đã sửa"


def test_seed_update_flag_overwrites(ctx):
    ctx.seed()
    with ctx.session_factory() as s:
        card = s.scalars(select(CardModel).where(CardModel.slug == "the-fool")).one()
        card.upright_meaning = "Admin đã sửa"
        s.commit()
    cards, spreads = load_data()
    with ctx.session_factory() as s:
        report = seed_database(s, cards, spreads, update=True)
    assert report.cards_updated == 78 and report.spreads_updated == 3
    with ctx.session_factory() as s:
        card = s.scalars(select(CardModel).where(CardModel.slug == "the-fool")).one()
        assert card.upright_meaning != "Admin đã sửa"
    assert counts(ctx) == (78, 3, 9)  # cập nhật vị trí không nhân đôi


def test_card_ids_follow_file_order_on_fresh_db(ctx):
    ctx.seed()
    with ctx.session_factory() as s:
        first = s.get(CardModel, 1)
        last = s.get(CardModel, 78)
    assert first.slug == "the-fool" and last.slug == "king-of-pentacles"
