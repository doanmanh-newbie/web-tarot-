from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://tarot:tarot@localhost:5432/tarot"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    gemini_api_key: str = ""
    ai_provider: str = "gemini"  # "gemini" | "offline" (diễn giải mẫu, không gọi mạng)
    gemini_model: str = "gemini-3.8-flash"
    gemini_max_output_tokens: int = 2048
    gemini_timeout_seconds: int = 20
    daily_reading_limit: int = 3
    app_timezone: str = "Asia/Ho_Chi_Minh"
    cors_origins: str = "http://localhost:5173"
    max_question_length: int = 300

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _jwt_secret_must_be_strong_outside_dev(self) -> "Settings":
        if self.app_env != "development" and (self.jwt_secret == "change-me" or len(self.jwt_secret) < 32):
            raise ValueError("JWT_SECRET phải đặt riêng và dài tối thiểu 32 ký tự khi không chạy development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
