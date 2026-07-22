"""Lead Card Builder — оркестрация генерации черновика первого сообщения
и сборки карточки лида для управляющего бота (ТЗ §5, §8.2, §9).

TODO(этап 1/2): реализовать сборку карточки (текст + кнопки) и вызов
llm.drafter.Drafter. Сетевой код (сам вызов LLM) — внутри llm/drafter.py.
"""

from __future__ import annotations

from core.models import Lead
from llm.drafter import Drafter


class DrafterAgent:
    """Строит черновик первого сообщения и карточку лида для оператора."""

    def __init__(self, drafter: Drafter | None = None) -> None:
        self.drafter = drafter or Drafter()

    def build_card(self, lead: Lead) -> str:
        """Возвращает готовый текст карточки лида (пример формата — §9 ТЗ)."""

        raise NotImplementedError(
            "TODO: self.drafter.draft_first_message(...) -> draft_text; "
            "создать Outreach(lead_id=lead.id, draft_text=...); "
            "отформатировать карточку по образцу §9 ТЗ"
        )
