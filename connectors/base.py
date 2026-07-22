"""Единый интерфейс коннектора источников данных (ТЗ §4, §5).

Каждый коннектор реализует `SourceConnector.poll() -> list[RawMessage]` и
работает по расписанию (Telegram — стрим в реальном времени поверх Telethon-
событий, Reddit/YouTube/VK — периодический опрос каждые 10–30 мин через
APScheduler, см. agents/monitor.py).

Этот файл — только интерфейс и DTO, без сетевой логики.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel

from core.models import Source


class RawMessage(BaseModel):
    """Унифицированный формат сообщения, отдаваемый любым коннектором (§5).

    Приводится к строке таблицы `messages` (core/models.py) слоем Ingest & Dedup
    (дедупликация — по паре source_id+ext_id, см. UniqueConstraint модели Message).
    """

    platform: str
    source_handle: str
    ext_id: str
    author_ext_id: str | None = None
    author_handle: str | None = None
    url: str | None = None
    text: str
    lang: str | None = None
    posted_at: datetime | None = None


class SourceConnector(ABC):
    """Базовый класс для всех коннекторов (§4 ТЗ).

    platform — константа платформы (например "telegram", "reddit"),
    используется для сопоставления с записями таблицы sources.
    """

    platform: str = "base"

    def __init__(self, source: Source) -> None:
        self.source = source

    @abstractmethod
    def poll(self) -> list[RawMessage]:
        """Возвращает новые сообщения источника с момента последнего опроса.

        Реализация должна сама обновлять `self.source.last_polled_at` (или это
        делает вызывающий Monitor-агент — решается на этапе реализации).
        Сетевые вызовы — только внутри конкретных коннекторов, не здесь.
        """
        raise NotImplementedError
