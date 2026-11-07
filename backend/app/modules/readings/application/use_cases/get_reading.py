from app.modules.readings.application.reading_details import ReadingDetails, ReadingDetailsBuilder
from app.modules.readings.domain.exceptions import ReadingNotFound
from app.modules.readings.domain.reading_repository import ReadingRepository


class GetReading:
    """Chi tiết một reading. Của người khác = ReadingNotFound (404), không phải 403, để không lộ sự tồn tại."""

    def __init__(self, readings: ReadingRepository, builder: ReadingDetailsBuilder) -> None:
        self._readings = readings
        self._builder = builder

    def execute(self, reading_id: int, user_id: int) -> ReadingDetails:
        reading = self._readings.get_by_id(reading_id)
        if reading is None or reading.user_id != user_id:
            raise ReadingNotFound(str(reading_id))
        return self._builder.build(reading)
