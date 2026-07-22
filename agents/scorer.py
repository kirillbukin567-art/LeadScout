"""Scorer-агент — оркестрация LLM-скоринга кандидатов (ТЗ §5, §8.1, §16).

Берёт сообщения со статусом-кандидатом (после TriggerFilter), вызывает
llm.scorer.Scorer, сохраняет результат: при `score >= threshold` создаёт
запись `Lead`, иначе помечает Message как scored без лида.

TODO(этап 1, MVP): реализовать запись в БД. Сетевой код (вызов LLM) —
внутри llm/scorer.py, здесь его тоже пока нет.
"""

from __future__ import annotations

from core.models import Message
from core.settings import get_settings
from llm.scorer import Scorer


class ScorerAgent:
    """Прогоняет кандидатов через LLM Scorer и материализует лидов в БД."""

    def __init__(self, scorer: Scorer | None = None, score_threshold: int | None = None) -> None:
        self.scorer = scorer or Scorer()
        self.score_threshold = score_threshold or get_settings().score_threshold

    def process_candidate(self, message: Message) -> None:
        """Скорит одно сообщение-кандидат; при прохождении порога создаёт Lead (§8.1)."""

        raise NotImplementedError(
            "TODO: self.scorer.score(message.text, meta) -> ScoringResult; "
            "если is_lead и score >= self.score_threshold и geo не blocked_geo -> "
            "создать Lead(...), иначе Message.status = MessageStatus.SCORED"
        )
