"""Telegram-коннектор (Telethon, MTProto) — мониторинг публичных чатов (§4 ТЗ, MVP).

Стрим в реальном времени: подписка на события новых сообщений в чатах из
реестра sources (platform="telegram"). Вступление в новые чаты — вручную,
лимит ≤ 2/день (§10, core/rate_limiter.py).

TODO(этап 1, MVP): реализовать через TelegramClient(settings.tg_session_monitor,
settings.tg_api_id, settings.tg_api_hash) и event handler NewMessage, с
буферизацией входящих в очередь для poll(). Сетевой код сюда пока не добавлен —
это только каркас интерфейса.
"""

from __future__ import annotations

from connectors.base import RawMessage, SourceConnector


class TelegramConnector(SourceConnector):
    """Мониторинговый коннектор Telegram (только чтение)."""

    platform = "telegram"

    def poll(self) -> list[RawMessage]:
        raise NotImplementedError(
            "TODO: реализовать через Telethon TelegramClient + NewMessage event handler"
        )
