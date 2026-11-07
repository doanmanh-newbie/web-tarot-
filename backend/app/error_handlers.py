"""Map lỗi nghiệp vụ của các module -> mã HTTP.

Đây là nơi duy nhất biết cả HTTP lẫn lỗi của mọi module. Thêm lỗi mới thì thêm một dòng vào _ERROR_MAP.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.auth.domain.exceptions import (
    EmailAlreadyUsed,
    InvalidCredentials,
    InvalidToken,
    WeakPassword,
)
from app.modules.cards.domain.exceptions import CardNotFound, InvalidCardMeaning
from app.modules.quota.domain.exceptions import DailyQuotaExceeded
from app.modules.readings.domain.exceptions import (
    DeckNotReady,
    InterpretationFailed,
    InvalidQuestion,
    ReadingNotFound,
)
from app.modules.spreads.domain.exceptions import SpreadNotFound
from app.shared.domain.exceptions import DomainError, NotAuthorized

# lỗi -> (mã HTTP, thông báo mặc định khi lỗi không kèm nội dung)
_ERROR_MAP: dict[type[DomainError], tuple[int, str]] = {
    InvalidCredentials: (401, "Email hoặc mật khẩu không đúng"),
    InvalidToken: (401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"),
    NotAuthorized: (403, "Bạn không có quyền thực hiện thao tác này"),
    EmailAlreadyUsed: (409, "Email này đã được đăng ký"),
    WeakPassword: (422, "Mật khẩu không đạt yêu cầu"),
    InvalidQuestion: (422, "Câu hỏi không hợp lệ"),
    ReadingNotFound: (404, "Không tìm thấy lần xem bài này"),
    CardNotFound: (404, "Không tìm thấy lá bài"),
    InvalidCardMeaning: (422, "Ý nghĩa lá bài không hợp lệ"),
    SpreadNotFound: (404, "Không tìm thấy kiểu trải bài"),
    DailyQuotaExceeded: (429, "Bạn đã dùng hết lượt hôm nay, quay lại vào ngày mai"),
    InterpretationFailed: (502, "Dịch vụ AI đang lỗi, vui lòng thử lại"),
    DeckNotReady: (503, "Bộ bài chưa sẵn sàng, vui lòng thử lại sau"),
}


def _lookup(exc: DomainError) -> tuple[int, str]:
    for cls in type(exc).__mro__:
        if cls in _ERROR_MAP:
            return _ERROR_MAP[cls]
    return 400, "Yêu cầu không hợp lệ"


def register_error_handlers(app: FastAPI) -> None:
    async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, DomainError)
        status, default_message = _lookup(exc)
        # Chỉ lỗi có thông báo thân thiện mới được hiện nguyên văn; còn lại dùng thông báo mặc định
        # (vd EmailAlreadyUsed mang theo email, không nên trả ra).
        own_message_errors = (WeakPassword, InvalidToken, NotAuthorized, InvalidCardMeaning, InvalidQuestion)
        shows_own_message = isinstance(exc, own_message_errors)
        message = str(exc) if shows_own_message and str(exc) else default_message
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return JSONResponse(status_code=status, content={"detail": message}, headers=headers)

    for cls in _ERROR_MAP:
        app.add_exception_handler(cls, handle_domain_error)
