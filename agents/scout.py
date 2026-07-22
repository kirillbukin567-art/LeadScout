"""Scout-агент — пополнение реестра источников (ТЗ §16).

Работает по расписанию (1 раз в день) и по команде `/discover <регион|язык|тема>`
из управляющего бота. Собирает кандидатов (упоминания/репосты в мониторимых
чатах, ссылки t.me, sidebar/wiki сабреддитов, похожие YouTube-каналы,
поисковые запросы), оценивает LLM (`source_score` 0–100) и присылает
оператору карточку источника с кнопками [Подключить]/[Отклонить]/[Отложить].

Гигиена реестра: источники без лидов (score≥порога) за 30 дней помечаются
`stale` и предлагаются к отключению.

TODO(этап 3): реализовать сбор кандидатов и LLM-оценку. Сетевой код пока не
добавлен — это только каркас.
"""

from __future__ import annotations

from pydantic import BaseModel

from core.models import DiscoveredBy


class SourceCandidate(BaseModel):
    """Кандидат в реестр источников до подтверждения оператором (§16)."""

    platform: str
    handle: str
    lang: str | None = None
    region: str | None = None
    source_score: int
    discovered_by: DiscoveredBy = DiscoveredBy.SCOUT
    verdict_reasons: list[str] = []


class ScoutAgent:
    """Ищет и оценивает новые источники для реестра `sources`."""

    def discover(
        self,
        region: str | None = None,
        lang: str | None = None,
        topic: str | None = None,
    ) -> list[SourceCandidate]:
        """Ручной запуск через `/discover <регион|язык|тема>` (§9, §16)."""

        raise NotImplementedError(
            "TODO: сбор кандидатов (TG-упоминания/ссылки, sidebar сабреддитов, похожие "
            "YT-каналы, веб-поиск) + LLM-оценка тематичности/живости/спам-плотности"
        )

    def run_daily(self) -> list[SourceCandidate]:
        """Плановый ежедневный прогон Discovery (§16)."""

        raise NotImplementedError("TODO: то же самое, но без явных фильтров региона/языка/темы")

    def mark_stale_sources(self) -> int:
        """Источники без лидов (score≥порога) за 30 дней → status=stale (§16)."""

        raise NotImplementedError(
            "TODO: SELECT sources WHERE stats_leads_30d == 0 -> status = SourceStatus.STALE"
        )
