from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.readings.domain.accuracy_stats import RatingRow
from app.modules.readings.domain.reading import AIStatus, Reading


class ReadingRepository(ABC):
    @abstractmethod
    def add_if_under_limit(
        self, reading: Reading, limit: int | None, window_start: datetime, window_end: datetime
    ) -> Reading | None:
        """Lưu reading NẾU số lượt của user trong [window_start, window_end) còn dưới `limit`.

        Kiểm tra và lưu phải nguyên tử (không để hai request đồng thời cùng lọt qua giới hạn).
        Trả None nếu đã hết lượt. `limit=None` = không giới hạn.
        Lượt đã xóa (xóa mềm) vẫn được tính, nên xóa lịch sử không hoàn lượt.
        """

    @abstractmethod
    def get_by_id(self, reading_id: int) -> Reading | None:
        """None nếu không có hoặc đã bị xóa."""

    @abstractmethod
    def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> list[Reading]:
        """Mới nhất trước; không gồm reading đã xóa."""

    @abstractmethod
    def update_interpretation(
        self, reading_id: int, text: str | None, status: AIStatus, prompt_version: str | None = None
    ) -> Reading: ...

    @abstractmethod
    def list_interpreted(self) -> list[RatingRow]:
        """Mọi reading đã có lời giải (DONE), chưa xóa, của tất cả người dùng: dữ liệu cho thống kê độ đúng."""

    @abstractmethod
    def update_accuracy(self, reading_id: int, accuracy: int) -> Reading: ...

    @abstractmethod
    def delete(self, reading_id: int) -> None:
        """Xóa mềm: ẩn khỏi lịch sử nhưng vẫn tính vào quota."""
