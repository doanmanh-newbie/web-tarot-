import secrets

from app.modules.readings.application.ports.random_source import RandomSource


class SecureRandomSource(RandomSource):
    """Bốc bài bằng nguồn ngẫu nhiên của hệ điều hành (module `secrets`), không dùng `random` thường."""

    def __init__(self) -> None:
        self._rng = secrets.SystemRandom()

    def draw_cards(self, deck_ids: list[int], count: int) -> list[tuple[int, bool]]:
        if count > len(deck_ids):
            raise ValueError("Không đủ lá bài để bốc")
        picked = self._rng.sample(list(deck_ids), count)  # không trùng lá
        return [(card_id, secrets.randbelow(2) == 1) for card_id in picked]  # mỗi lá 50% ngược
