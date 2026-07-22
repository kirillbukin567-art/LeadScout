"""Конфигурация приложения на pydantic-settings (ТЗ §11).

Все секреты читаются ИСКЛЮЧИТЕЛЬНО из .env — жёсткое правило проекта,
хардкодить ключи/токены в коде нельзя. См. .env.example для полного списка
переменных и пояснений к ним.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

Mode = Literal["m1", "m2", "m3"]


class Settings(BaseSettings):
    """Единая точка доступа к конфигурации приложения."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Claude / Anthropic (§8) -------------------------------------------------
    anthropic_api_key: str

    # --- Telegram: Telethon (мониторинг + отправка) и aiogram (управляющий бот) ---
    tg_api_id: int
    tg_api_hash: str
    tg_session_monitor: str = "monitor"
    tg_session_sender: str = "sender"
    control_bot_token: str
    operator_tg_id: int

    # --- Reddit (PRAW) ------------------------------------------------------------
    reddit_client_id: str
    reddit_client_secret: str

    # --- YouTube Data API v3 / VK API (опциональны на этапе MVP) ------------------
    youtube_api_key: str | None = None
    vk_token: str | None = None

    # --- Прочие параметры приложения (не входят в §11, есть значения по умолчанию) -
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'leadscout.db').as_posix()}"
    log_level: str = "INFO"
    default_mode: Mode = "m1"
    score_threshold: int = Field(default=55, ge=0, le=100)
    operator_timezone: str = "Europe/Moscow"

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    """Кэшированный доступ к настройкам (читаем .env один раз за процесс)."""

    return Settings()  # type: ignore[call-arg]  # значения приходят из .env
