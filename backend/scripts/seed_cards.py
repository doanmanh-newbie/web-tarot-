"""Nạp 78 lá bài + các kiểu trải bài vào DB.

Chạy:
    python -m scripts.seed_cards            # thêm dữ liệu còn thiếu, KHÔNG đụng dữ liệu đã có
    python -m scripts.seed_cards --update   # ghi đè dữ liệu đã có bằng nội dung trong file JSON

Vì sao mặc định không ghi đè: admin có thể đã sửa ý nghĩa lá bài qua giao diện; chạy lại seed
(ví dụ mỗi lần deploy) không được xóa mất chỉnh sửa đó. Dùng --update khi chủ động muốn đặt lại.
Script idempotent: chạy nhiều lần không nhân đôi dữ liệu. Khóa nhận diện là `slug`.
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.cards.infrastructure.models import CardModel
from app.modules.spreads.infrastructure.models import SpreadModel, SpreadPositionModel

DATA_DIR = Path(__file__).parent / "data"
SUITS = ("wands", "cups", "swords", "pentacles")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CARD_FIELDS = (
    "name", "name_vi", "arcana", "suit", "number", "upright_meaning", "reversed_meaning", "image_url"
)


@dataclass
class SeedReport:
    cards_added: int = 0
    cards_updated: int = 0
    cards_skipped: int = 0
    spreads_added: int = 0
    spreads_updated: int = 0
    spreads_skipped: int = 0

    def __str__(self) -> str:
        return (
            f"Lá bài: +{self.cards_added} mới, {self.cards_updated} cập nhật, {self.cards_skipped} giữ nguyên\n"
            f"Kiểu trải bài: +{self.spreads_added} mới, {self.spreads_updated} cập nhật, "
            f"{self.spreads_skipped} giữ nguyên"
        )


def load_data() -> tuple[list[dict], list[dict]]:
    cards = json.loads((DATA_DIR / "cards.json").read_text(encoding="utf-8"))
    spreads = json.loads((DATA_DIR / "spreads.json").read_text(encoding="utf-8"))
    return cards, spreads


def validate_cards(cards: list[dict]) -> list[str]:
    """Kiểm tra dữ liệu bộ bài; trả về danh sách lỗi (rỗng = hợp lệ)."""
    errors: list[str] = []
    if len(cards) != 78:
        errors.append(f"Bộ bài phải có 78 lá, hiện có {len(cards)}")
    slugs = [c.get("slug", "") for c in cards]
    for slug in {s for s in slugs if slugs.count(s) > 1}:
        errors.append(f"Trùng slug: {slug}")
    groups: dict[str | None, list[int]] = {}
    for c in cards:
        slug = c.get("slug", "?")
        if not SLUG_RE.match(slug):
            errors.append(f"[{slug}] slug không hợp lệ")
        for key in ("name", "name_vi", "upright_meaning", "reversed_meaning"):
            if not str(c.get(key, "")).strip():
                errors.append(f"[{slug}] thiếu {key}")
        arcana, suit, number = c.get("arcana"), c.get("suit"), c.get("number")
        if arcana == "major":
            if suit is not None:
                errors.append(f"[{slug}] Major Arcana không có suit")
            groups.setdefault(None, []).append(number)
        elif arcana == "minor":
            if suit not in SUITS:
                errors.append(f"[{slug}] suit không hợp lệ: {suit}")
            groups.setdefault(suit, []).append(number)
        else:
            errors.append(f"[{slug}] arcana không hợp lệ: {arcana}")
    if sorted(groups.get(None, [])) != list(range(0, 22)):
        errors.append("Major Arcana phải có đủ số 0-21, mỗi số một lá")
    for suit in SUITS:
        if sorted(groups.get(suit, [])) != list(range(1, 15)):
            errors.append(f"Bộ {suit} phải có đủ số 1-14, mỗi số một lá")
    return errors


def validate_spreads(spreads: list[dict]) -> list[str]:
    errors: list[str] = []
    slugs = [s.get("slug", "") for s in spreads]
    if not spreads:
        errors.append("Cần ít nhất một kiểu trải bài")
    for slug in {s for s in slugs if slugs.count(s) > 1}:
        errors.append(f"Trùng slug kiểu trải bài: {slug}")
    for s in spreads:
        slug = s.get("slug", "?")
        if not SLUG_RE.match(slug):
            errors.append(f"[{slug}] slug không hợp lệ")
        if not str(s.get("name", "")).strip():
            errors.append(f"[{slug}] thiếu name")
        positions = s.get("positions", [])
        if not positions:
            errors.append(f"[{slug}] cần ít nhất một vị trí")
        labels = [p.get("label", "") for p in positions]
        if any(not label.strip() for label in labels) or len(set(labels)) != len(labels):
            errors.append(f"[{slug}] nhãn vị trí phải có và không trùng nhau")
    return errors


def _positions(data: dict) -> list[SpreadPositionModel]:
    return [
        SpreadPositionModel(position_index=i, label=p["label"], description=p.get("description", ""))
        for i, p in enumerate(data["positions"])
    ]


def seed_database(session: Session, cards: list[dict], spreads: list[dict], update: bool = False) -> SeedReport:
    report = SeedReport()

    existing_cards = {c.slug: c for c in session.scalars(select(CardModel))}
    for data in cards:
        row = existing_cards.get(data["slug"])
        values = {k: data.get(k) for k in CARD_FIELDS}
        if row is None:
            session.add(CardModel(slug=data["slug"], **values))
            report.cards_added += 1
        elif update:
            for key, value in values.items():
                setattr(row, key, value)
            report.cards_updated += 1
        else:
            report.cards_skipped += 1

    stmt = select(SpreadModel).options(selectinload(SpreadModel.positions))
    existing_spreads = {s.slug: s for s in session.scalars(stmt)}
    for data in spreads:
        row = existing_spreads.get(data["slug"])
        if row is None:
            session.add(
                SpreadModel(
                    slug=data["slug"],
                    name=data["name"],
                    description=data.get("description", ""),
                    positions=_positions(data),
                )
            )
            report.spreads_added += 1
        elif update:
            row.name = data["name"]
            row.description = data.get("description", "")
            row.positions.clear()
            session.flush()  # xóa vị trí cũ trước khi thêm vị trí mới (tránh đụng ràng buộc UNIQUE)
            row.positions.extend(_positions(data))
            report.spreads_updated += 1
        else:
            report.spreads_skipped += 1

    session.commit()
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nạp bộ bài Tarot và các kiểu trải bài")
    parser.add_argument("--update", action="store_true", help="ghi đè dữ liệu đã có bằng nội dung trong JSON")
    args = parser.parse_args(argv)

    cards, spreads = load_data()
    errors = validate_cards(cards) + validate_spreads(spreads)
    if errors:
        print("Dữ liệu seed không hợp lệ:")
        for err in errors:
            print(f"  - {err}")
        return 1

    from app.shared.infrastructure.db.session import SessionLocal

    with SessionLocal() as session:
        report = seed_database(session, cards, spreads, update=args.update)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
