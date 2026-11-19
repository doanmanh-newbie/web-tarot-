from app.modules.readings.application.reading_details import ReadingDetails, ReadingDetailsBuilder
from app.modules.readings.domain.exceptions import InvalidAccuracy, ReadingNotFound
from app.modules.readings.domain.reading import AIStatus
from app.modules.readings.domain.reading_repository import ReadingRepository


class RateReading:
    """Người dùng tự chấm lời giải đúng bao nhiêu % (0-100) để có số liệu đánh giá chất lượng lời giải.

    - Chỉ chấm được reading của chính mình (của người khác coi như không tồn tại).
    - Chỉ chấm khi đã có lời giải (DONE). Chấm lại thì ghi đè điểm cũ.
    """

    def __init__(self, readings: ReadingRepository, builder: ReadingDetailsBuilder) -> None:
        self._readings = readings
        self._builder = builder

    def execute(self, reading_id: int, user_id: int, accuracy: int) -> ReadingDetails:
        if not 0 <= accuracy <= 100:
            raise InvalidAccuracy("Mức đúng phải từ 0 đến 100%")
        reading = self._readings.get_by_id(reading_id)
        if reading is None or reading.user_id != user_id:
            raise ReadingNotFound(str(reading_id))
        if reading.ai_status is not AIStatus.DONE:
            raise InvalidAccuracy("Lần bốc này chưa có lời giải để đánh giá")
        return self._builder.build(self._readings.update_accuracy(reading_id, accuracy))
