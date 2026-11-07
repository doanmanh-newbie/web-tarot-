from types import SimpleNamespace

import pytest

from app.modules.readings.application.ports.ai_interpreter import CardForPrompt
from app.modules.readings.domain.exceptions import InterpretationFailed
from app.modules.readings.infrastructure.ai.gemini_interpreter import GeminiInterpreter, UnconfiguredInterpreter
from app.modules.readings.infrastructure.ai.offline_interpreter import OfflineInterpreter

CARDS = [CardForPrompt("Chàng Khờ (The Fool)", "Quá khứ", "", False, "Khởi đầu mới")]


class FakeModels:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.kwargs = text, error, None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


def make(text="Diễn giải", error=None, timeout=20):
    models = FakeModels(text, error)
    return GeminiInterpreter(SimpleNamespace(models=models), "gemini-test", timeout, 512), models


def test_returns_stripped_text():
    gem, _ = make("  Lời diễn giải  \n")
    assert gem.interpret("q", "Một lá", CARDS) == "Lời diễn giải"


def test_sends_model_prompts_and_limits():
    gem, models = make()
    gem.interpret("Tình yêu?", "Một lá", CARDS)
    kw = models.kwargs
    assert kw["model"] == "gemini-test"
    assert "Khởi đầu mới" in kw["contents"] and "Tình yêu?" in kw["contents"]
    cfg = kw["config"]
    assert "Tình yêu?" not in cfg.system_instruction      # input người dùng không lọt vào system prompt
    assert cfg.max_output_tokens == 512
    assert cfg.http_options.timeout == 20000               # SDK tính bằng mili-giây


@pytest.mark.parametrize("error", [TimeoutError("hết giờ"), ConnectionError("mất mạng"), RuntimeError("429 quota")])
def test_any_sdk_error_becomes_interpretation_failed(error):
    gem, _ = make(error=error)
    with pytest.raises(InterpretationFailed):
        gem.interpret("q", "Một lá", CARDS)


@pytest.mark.parametrize("text", [None, "", "   \n"])
def test_empty_or_blocked_answer_is_a_failure(text):
    gem, _ = make(text=text)
    with pytest.raises(InterpretationFailed):
        gem.interpret("q", "Một lá", CARDS)


def test_unconfigured_interpreter_fails_cleanly():
    with pytest.raises(InterpretationFailed):
        UnconfiguredInterpreter().interpret("q", "Một lá", CARDS)


def test_offline_interpreter_uses_base_meanings():
    text = OfflineInterpreter().interpret("q", "Một lá", CARDS)
    assert "Khởi đầu mới" in text and "Chàng Khờ" in text
