from abc import ABC, abstractmethod
from datetime import datetime


class ReadingCounter(ABC):
    @abstractmethod
    def count_by_user_between(self, user_id: int, start: datetime, end: datetime) -> int:
        """Số lượt bốc của user trong [start, end). Module `readings` cài đặt."""
