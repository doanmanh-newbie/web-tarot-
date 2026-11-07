from dataclasses import dataclass

ARCANA_MAJOR = "major"
ARCANA_MINOR = "minor"
SUITS = ("wands", "cups", "swords", "pentacles")


@dataclass
class Card:
    id: int
    slug: str              # khóa tự nhiên, vd "the-fool", "ace-of-wands" (seed dùng để upsert)
    name: str              # tên tiếng Anh, vd "The Fool"
    name_vi: str           # tên tiếng Việt, vd "Chàng Khờ"
    arcana: str            # ARCANA_MAJOR | ARCANA_MINOR
    suit: str | None       # một trong SUITS; None với Major Arcana
    number: int            # Major: 0-21; Minor: 1-14 (Ace=1, Page=11, Knight=12, Queen=13, King=14)
    upright_meaning: str
    reversed_meaning: str
    image_url: str | None = None

    def meaning(self, is_reversed: bool) -> str:
        """Ý nghĩa gốc theo chiều bài (dùng để nhét vào prompt cho AI)."""
        return self.reversed_meaning if is_reversed else self.upright_meaning
