import logging

from google import genai
from google.genai import types

from app.modules.readings.application.ports.ai_interpreter import AIInterpreter, CardForPrompt
from app.modules.readings.domain.exceptions import InterpretationFailed
from app.modules.readings.infrastructure.ai.prompt_builder import (
    PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
    clean_output,
)

logger = logging.getLogger(__name__)

# Lỗi tạm thời phía Google (quá tải, hết giờ, giới hạn tốc độ): thử model dự phòng kế tiếp
_RETRYABLE_CODES = {429, 500, 503, 504}


def _retryable(exc: Exception) -> bool:
    return isinstance(exc, TimeoutError) or getattr(exc, "code", None) in _RETRYABLE_CODES


class GeminiInterpreter(AIInterpreter):
    """Gọi Gemini qua SDK google-genai. Mọi lỗi (mạng, hết quota, bị chặn nội dung, hết giờ, rỗng) đều
    được đổi thành InterpretationFailed để tầng trên xử lý thống nhất (đánh dấu FAILED, cho "Giải lại").
    Model chính quá tải/hết giờ thì lần lượt thử các model dự phòng (fallback_models) trước khi báo lỗi.
    Không ghi câu hỏi của người dùng và API key vào log."""

    version = PROMPT_VERSION

    def __init__(
        self,
        client: genai.Client,
        model: str,
        timeout_seconds: int,
        max_output_tokens: int,
        fallback_models: tuple[str, ...] = (),
    ) -> None:
        self._client = client
        self._models = [model, *(m for m in fallback_models if m and m != model)]
        self._timeout_ms = int(timeout_seconds * 1000)  # SDK tính timeout bằng mili-giây
        self._max_output_tokens = max_output_tokens

    def interpret(self, question: str, spread_name: str, cards: list[CardForPrompt]) -> str:
        config = types.GenerateContentConfig(
            system_instruction=build_system_prompt(),
            temperature=0.6,  # thấp hơn để bám nghĩa lá, bớt bay bổng
            max_output_tokens=self._max_output_tokens,
            http_options=types.HttpOptions(timeout=self._timeout_ms),
        )
        contents = build_user_prompt(question, spread_name, cards)
        for i, model in enumerate(self._models):
            try:
                response = self._client.models.generate_content(model=model, contents=contents, config=config)
                text = clean_output(response.text or "")
                break
            except Exception as exc:  # ranh giới với dịch vụ ngoài: bắt rộng có chủ đích
                logger.warning("Gemini lỗi (%s): %s (code=%s)", model, type(exc).__name__, getattr(exc, "code", None))
                if not _retryable(exc) or i == len(self._models) - 1:
                    raise InterpretationFailed("Không gọi được dịch vụ AI") from exc
        if not text:
            logger.warning("Gemini trả nội dung rỗng (có thể bị chặn bởi bộ lọc an toàn)")
            raise InterpretationFailed("AI không trả về nội dung")
        return text


class UnconfiguredInterpreter(AIInterpreter):
    """Dùng khi chưa có GEMINI_API_KEY: app vẫn chạy, bài vẫn bốc và lưu được, chỉ phần AI báo lỗi."""

    def interpret(self, question: str, spread_name: str, cards: list[CardForPrompt]) -> str:
        raise InterpretationFailed("Chưa cấu hình GEMINI_API_KEY")
