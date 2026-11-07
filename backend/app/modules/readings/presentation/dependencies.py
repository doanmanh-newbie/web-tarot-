"""Lắp ráp module readings: repository, Gemini, random + use case (kèm use case của cards/spreads/quota)."""
from functools import lru_cache

from fastapi import Depends
from google import genai
from sqlalchemy.orm import Session

from app.config import get_settings
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.presentation.dependencies import get_card_repository
from app.modules.quota.application.use_cases.get_quota import GetQuota
from app.modules.quota.domain.quota_policy import QuotaConfig
from app.modules.readings.application.ports.ai_interpreter import AIInterpreter
from app.modules.readings.application.ports.random_source import RandomSource
from app.modules.readings.application.reading_details import ReadingDetailsBuilder
from app.modules.readings.application.use_cases.delete_reading import DeleteReading
from app.modules.readings.application.use_cases.draw_reading import DrawReading
from app.modules.readings.application.use_cases.get_reading import GetReading
from app.modules.readings.application.use_cases.interpret_reading import InterpretReading
from app.modules.readings.application.use_cases.list_readings import ListReadings
from app.modules.readings.domain.reading_repository import ReadingRepository
from app.modules.readings.infrastructure.ai.gemini_interpreter import GeminiInterpreter, UnconfiguredInterpreter
from app.modules.readings.infrastructure.ai.offline_interpreter import OfflineInterpreter
from app.modules.readings.infrastructure.secure_random_source import SecureRandomSource
from app.modules.readings.infrastructure.sqlalchemy_reading_repository import SqlAlchemyReadingRepository
from app.modules.spreads.domain.spread_repository import SpreadRepository
from app.modules.spreads.presentation.dependencies import get_spread_repository
from app.shared.application.ports.clock import Clock
from app.shared.presentation.dependencies import get_clock, get_db_session


@lru_cache
def _gemini_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def get_ai_interpreter() -> AIInterpreter:
    settings = get_settings()
    if settings.ai_provider == "offline":
        return OfflineInterpreter()
    if not settings.gemini_api_key:
        return UnconfiguredInterpreter()
    return GeminiInterpreter(
        _gemini_client(settings.gemini_api_key),
        settings.gemini_model,
        settings.gemini_timeout_seconds,
        settings.gemini_max_output_tokens,
    )


def get_random_source() -> RandomSource:
    return SecureRandomSource()


def get_quota_config() -> QuotaConfig:
    settings = get_settings()
    return QuotaConfig(daily_limit=settings.daily_reading_limit, tz_name=settings.app_timezone)


def get_reading_repository(session: Session = Depends(get_db_session)) -> SqlAlchemyReadingRepository:
    return SqlAlchemyReadingRepository(session)


def get_details_builder(
    spreads: SpreadRepository = Depends(get_spread_repository),
    cards: CardRepository = Depends(get_card_repository),
) -> ReadingDetailsBuilder:
    return ReadingDetailsBuilder(spreads, cards)


def get_interpret_reading(
    readings: ReadingRepository = Depends(get_reading_repository),
    builder: ReadingDetailsBuilder = Depends(get_details_builder),
    ai: AIInterpreter = Depends(get_ai_interpreter),
) -> InterpretReading:
    return InterpretReading(readings, builder, ai)


def get_draw_reading(
    spreads: SpreadRepository = Depends(get_spread_repository),
    cards: CardRepository = Depends(get_card_repository),
    readings: ReadingRepository = Depends(get_reading_repository),
    random_source: RandomSource = Depends(get_random_source),
    interpret: InterpretReading = Depends(get_interpret_reading),
    clock: Clock = Depends(get_clock),
    quota: QuotaConfig = Depends(get_quota_config),
) -> DrawReading:
    return DrawReading(
        spreads, cards, readings, random_source, interpret, clock, quota, get_settings().max_question_length
    )


def get_list_readings(
    readings: ReadingRepository = Depends(get_reading_repository),
    builder: ReadingDetailsBuilder = Depends(get_details_builder),
) -> ListReadings:
    return ListReadings(readings, builder)


def get_get_reading(
    readings: ReadingRepository = Depends(get_reading_repository),
    builder: ReadingDetailsBuilder = Depends(get_details_builder),
) -> GetReading:
    return GetReading(readings, builder)


def get_delete_reading(readings: ReadingRepository = Depends(get_reading_repository)) -> DeleteReading:
    return DeleteReading(readings)


def get_get_quota(
    counter: SqlAlchemyReadingRepository = Depends(get_reading_repository),
    clock: Clock = Depends(get_clock),
    quota: QuotaConfig = Depends(get_quota_config),
) -> GetQuota:
    return GetQuota(counter, clock, quota)
