from app.modules.cards.domain.card_repository import CardRepository
from app.modules.quota.domain.exceptions import DailyQuotaExceeded
from app.modules.quota.domain.quota_policy import QuotaConfig, day_bounds
from app.modules.readings.application.ports.random_source import RandomSource
from app.modules.readings.application.reading_details import ReadingDetails
from app.modules.readings.application.use_cases.interpret_reading import InterpretReading
from app.modules.readings.domain.exceptions import DeckNotReady
from app.modules.readings.domain.question_policy import clean_question
from app.modules.readings.domain.reading import DrawnCard, Reading
from app.modules.readings.domain.reading_repository import ReadingRepository
from app.modules.spreads.domain.exceptions import SpreadNotFound
from app.modules.spreads.domain.spread_repository import SpreadRepository
from app.shared.application.ports.clock import Clock


class DrawReading:
    """Bốc bài + lưu + nhờ AI diễn giải.

    Thứ tự quan trọng:
      1. Kiểm tra đầu vào (câu hỏi, kiểu trải bài) TRƯỚC khi đụng tới quota, nên lỗi đầu vào không mất lượt.
      2. Bốc bài ở server (không tin client).
      3. Lưu reading kèm kiểm tra quota trong MỘT bước nguyên tử (repository lo), chống bấm đồng thời để lách giới hạn.
      4. SAU KHI đã lưu mới gọi AI. AI lỗi thì bài vẫn còn, reading ở trạng thái FAILED để "Giải lại",
         và lượt đã tính (người dùng đã thực sự rút bài). Không bốc lại, không mất lượt oan.
    """

    def __init__(
        self,
        spreads: SpreadRepository,
        cards: CardRepository,
        readings: ReadingRepository,
        random_source: RandomSource,
        interpret: InterpretReading,
        clock: Clock,
        quota: QuotaConfig,
        max_question_length: int,
    ) -> None:
        self._spreads = spreads
        self._cards = cards
        self._readings = readings
        self._random = random_source
        self._interpret = interpret
        self._clock = clock
        self._quota = quota
        self._max_question_length = max_question_length

    def execute(self, user_id: int, spread_id: int, question: str, unlimited: bool = False) -> ReadingDetails:
        question = clean_question(question, self._max_question_length)
        spread = self._spreads.get_by_id(spread_id)
        if spread is None:
            raise SpreadNotFound(str(spread_id))

        deck_ids = self._cards.list_ids()
        if len(deck_ids) < spread.card_count:
            raise DeckNotReady("Bộ bài chưa được nạp đủ, hãy chạy seed")

        now = self._clock.now()
        drawn = [
            DrawnCard(card_id=card_id, position_index=index, is_reversed=is_reversed)
            for index, (card_id, is_reversed) in enumerate(self._random.draw_cards(deck_ids, spread.card_count))
        ]
        reading = Reading(
            id=None, user_id=user_id, spread_id=spread.id, question=question, drawn_cards=drawn, created_at=now
        )

        window_start, window_end = day_bounds(now, self._quota.tz_name)
        limit = None if unlimited else self._quota.daily_limit
        saved = self._readings.add_if_under_limit(reading, limit, window_start, window_end)
        if saved is None:
            raise DailyQuotaExceeded(f"Đã dùng hết {self._quota.daily_limit} lượt hôm nay")

        return self._interpret.execute(saved.id, user_id)
