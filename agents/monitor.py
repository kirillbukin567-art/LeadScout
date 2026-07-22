"""Monitor-агент — сбор сообщений из коннекторов, Ingest & Dedup (ТЗ §5, §16).

Мультиагентная архитектура (§16): Scout (поиск источников) → **Monitor**
(сбор сообщений) → Scorer (квалификация) → Drafter/Replier (тексты) →
оркестрация через общую БД и управляющий бот.

Планирование: Telegram — стрим в реальном времени (коннектор сам подписан на
события), Reddit/YouTube/VK/generic — периодический опрос через APScheduler
каждые 10–30 мин (§4).

TODO(этап 1, MVP): реализовать цикл опроса коннекторов + запись новых
Message с дедупом по (source_id, ext_id) + прогон через TriggerFilter.
Сетевой код пока не добавлен — это только каркас оркестрации.
"""

from __future__ import annotations

from connectors.base import SourceConnector
from core.trigger_filter import TriggerFilter


class MonitorAgent:
    """Опрашивает набор коннекторов и складывает новые сообщения в БД."""

    def __init__(
        self,
        connectors: list[SourceConnector],
        trigger_filter: TriggerFilter | None = None,
    ) -> None:
        self.connectors = connectors
        self.trigger_filter = trigger_filter or TriggerFilter.from_yaml()

    def run_once(self) -> int:
        """Опрашивает все коннекторы, сохраняет новые сообщения (дедуп),
        прогоняет их через триггер-фильтр и обновляет статус (§5, §7).

        Возвращает количество новых сохранённых сообщений.
        """

        raise NotImplementedError(
            "TODO: для каждого connector.poll() -> RawMessage; upsert в Message с "
            "дедупом по UniqueConstraint(source_id, ext_id); trigger_filter.check(...) "
            "-> обновление Message.status (filtered_out | scored-кандидат)"
        )

    def schedule(self, scheduler) -> None:  # scheduler: apscheduler.schedulers.base.BaseScheduler
        """Регистрирует периодический опрос в APScheduler (интервалы — по платформе)."""

        raise NotImplementedError("TODO: scheduler.add_job(self.run_once, 'interval', minutes=...)")
