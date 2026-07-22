"""LLM Drafter — генератор черновика первого сообщения (ТЗ §8.2).

Отдельный промпт (llm/prompts/draft_message.md), модель Claude Sonnet.
Черновик — 2-3 предложения на языке лида, без ссылки, тон/структура по
`recommended_method`, угол по `recommended_angle`, соблюдение стоп-листа.

TODO(этап 2): реализовать вызов LLM. Сетевой код пока не добавлен.
"""

from __future__ import annotations

from pathlib import Path

from llm.client import ClaudeClient, MODEL_DRAFTER
from llm.schemas import ScoringResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DRAFT_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "draft_message.md"


class Drafter:
    """Обёртка над LLM-вызовом генерации черновика первого касания."""

    def __init__(self, client: ClaudeClient | None = None) -> None:
        self.client = client or ClaudeClient()

    def draft_first_message(self, scoring: ScoringResult, message_text: str, context: dict) -> str:
        """context: доп. контекст карточки лида (чат/тема, платформа и т.п.)."""

        raise NotImplementedError(
            "TODO: system_prompt = DRAFT_SYSTEM_PROMPT_PATH.read_text(); "
            "вызов ClaudeClient.complete(model=MODEL_DRAFTER, ...)"
        )
