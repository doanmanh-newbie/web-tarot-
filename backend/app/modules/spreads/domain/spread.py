from dataclasses import dataclass, field


@dataclass
class SpreadPosition:
    index: int             # bắt đầu từ 0
    label: str             # vd "Quá khứ"
    description: str = ""  # vd "Điều đã ảnh hưởng đến tình huống" (đưa vào prompt cho AI)


@dataclass
class Spread:
    id: int
    slug: str
    name: str
    description: str = ""
    positions: list[SpreadPosition] = field(default_factory=list)

    @property
    def card_count(self) -> int:
        return len(self.positions)
