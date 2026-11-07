from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CardForPrompt:
    name: str                  # vd "Chàng Khờ (The Fool)"
    position_label: str        # vd "Quá khứ"
    position_description: str  # vd "Điều đã ảnh hưởng đến tình huống hiện tại"
    is_reversed: bool
    base_meaning: str          # ý nghĩa gốc từ DB, ĐÚNG chiều xuôi/ngược của lá


class AIInterpreter(ABC):
    @abstractmethod
    def interpret(self, question: str, spread_name: str, cards: list[CardForPrompt]) -> str:
        """Trả về lời diễn giải. Raise InterpretationFailed nếu lỗi/timeout/nội dung rỗng."""
