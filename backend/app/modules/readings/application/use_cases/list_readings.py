from app.modules.readings.application.reading_details import ReadingDetails, ReadingDetailsBuilder
from app.modules.readings.domain.reading_repository import ReadingRepository


class ListReadings:
    """Lịch sử của chính user, mới nhất trước."""

    def __init__(self, readings: ReadingRepository, builder: ReadingDetailsBuilder) -> None:
        self._readings = readings
        self._builder = builder

    def execute(self, user_id: int, limit: int = 20, offset: int = 0) -> list[ReadingDetails]:
        return self._builder.build_many(self._readings.list_by_user(user_id, limit, offset))
