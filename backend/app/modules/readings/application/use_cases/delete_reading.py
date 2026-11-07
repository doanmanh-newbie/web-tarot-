from app.modules.readings.domain.exceptions import ReadingNotFound
from app.modules.readings.domain.reading_repository import ReadingRepository


class DeleteReading:
    """Xóa khỏi lịch sử (xóa mềm). Vẫn tính vào quota để không thể "bốc rồi xóa" nhằm lách giới hạn."""

    def __init__(self, readings: ReadingRepository) -> None:
        self._readings = readings

    def execute(self, reading_id: int, user_id: int) -> None:
        reading = self._readings.get_by_id(reading_id)
        if reading is None or reading.user_id != user_id:
            raise ReadingNotFound(str(reading_id))
        self._readings.delete(reading_id)
