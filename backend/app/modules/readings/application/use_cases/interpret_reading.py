import logging
from dataclasses import replace

from app.modules.readings.application.ports.ai_interpreter import AIInterpreter, CardForPrompt
from app.modules.readings.application.reading_details import ReadingDetails, ReadingDetailsBuilder
from app.modules.readings.domain.accuracy_stats import split_question
from app.modules.readings.domain.exceptions import InterpretationFailed, ReadingNotFound
from app.modules.readings.domain.reading import AIStatus
from app.modules.readings.domain.reading_repository import ReadingRepository

logger = logging.getLogger(__name__)

# Chủ đề frontend gửi -> khóa nghĩa theo chủ đề trong cards.details (Học tập/Chung chưa có dữ liệu riêng)
_TOPIC_KEYS = {"Tình cảm": "love", "Công việc": "career", "Tài chính": "finance", "Sức khỏe": "health"}


def _prompt_card(c, topic_key: str | None) -> CardForPrompt:
    details = c.card.details or {}
    side = "reversed" if c.is_reversed else "upright"
    return CardForPrompt(
        name=f"{c.card.name_vi} ({c.card.name})",
        position_label=c.position_label,
        position_description=c.position_description,
        is_reversed=c.is_reversed,
        base_meaning=c.meaning,
        keywords=", ".join(details.get(f"keywords_{side}") or []),
        topic_meaning=(details.get(topic_key) or {}).get(side, "") if topic_key else "",
    )


class InterpretReading:
    """Nhờ AI diễn giải một reading đã có. Dùng cho lần đầu (sau khi bốc) và cho nút "Giải lại".

    - KHÔNG bốc lại bài, KHÔNG tính thêm lượt (bài đã được lưu và đã tính lượt lúc bốc).
    - AI lỗi thì không ném lỗi ra ngoài: reading được đánh dấu FAILED, người dùng bấm "Giải lại" sau.
    - Reading đã có diễn giải (DONE) thì trả luôn, không gọi AI lần nữa (tiết kiệm quota Gemini).
    - Reading của người khác coi như không tồn tại (ReadingNotFound), không lộ sự tồn tại.
    """

    def __init__(self, readings: ReadingRepository, builder: ReadingDetailsBuilder, ai: AIInterpreter) -> None:
        self._readings = readings
        self._builder = builder
        self._ai = ai

    def describe(self, reading) -> ReadingDetails:
        """Chi tiết reading (lá, vị trí, ý nghĩa) mà không gọi AI."""
        return self._builder.build(reading)

    def execute(self, reading_id: int, user_id: int) -> ReadingDetails:
        reading = self._readings.get_by_id(reading_id)
        if reading is None or reading.user_id != user_id:
            raise ReadingNotFound(str(reading_id))

        details = self._builder.build(reading)
        if reading.ai_status is AIStatus.DONE and reading.ai_interpretation:
            return details

        topic_key = _TOPIC_KEYS.get(split_question(reading.question)[1])
        prompt_cards = [_prompt_card(c, topic_key) for c in details.cards]
        try:
            text = self._ai.interpret(reading.question, details.spread.name, prompt_cards)
            if not text or not text.strip():
                raise InterpretationFailed("AI trả về nội dung rỗng")
        except InterpretationFailed as exc:
            logger.warning("Diễn giải thất bại cho reading %s: %s", reading_id, exc)
            updated = self._readings.update_interpretation(reading_id, None, AIStatus.FAILED)
        else:
            updated = self._readings.update_interpretation(reading_id, text.strip(), AIStatus.DONE, self._ai.version)
        return replace(details, reading=updated)
