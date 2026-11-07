from abc import ABC, abstractmethod


class RandomSource(ABC):
    @abstractmethod
    def draw_cards(self, deck_ids: list[int], count: int) -> list[tuple[int, bool]]:
        """Bốc `count` lá không trùng; mỗi phần tử = (card_id, is_reversed)."""
