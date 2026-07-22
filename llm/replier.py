"""LLM Replier — генератор реплик в активном диалоге (ТЗ §8.3).

Вход: транскрипт диалога + карточка лида + knowledge/bingx_facts.md.
Выход: основная реплика + альтернатива (llm.schemas.DialogueReplyResult).
Правила раскрытия партнёрства, ссылки только после интереса, гео-квалификация,
cards_restricted-оговорка и эскалация при вопросах вне базы знаний — все в
системном промпте llm/prompts/dialogue_reply.md, не в коде (правило проекта).

TODO(этап 2): реализовать вызов LLM. Сетевой код пока не добавлен.
"""

from __future__ import annotations

from pathlib import Path

from llm.client import ClaudeClient, MODEL_DRAFTER
from llm.schemas import DialogueReplyResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DIALOGUE_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "dialogue_reply.md"
KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "bingx_facts.md"


class Replier:
    """Обёртка над LLM-вызовом генерации реплики в диалоге."""

    def __init__(self, client: ClaudeClient | None = None) -> None:
        self.client = client or ClaudeClient()

    def reply(self, transcript: list[dict], lead_card: dict) -> DialogueReplyResult:
        raise NotImplementedError(
            "TODO: system_prompt = DIALOGUE_SYSTEM_PROMPT_PATH.read_text() + "
            "KNOWLEDGE_BASE_PATH.read_text(); вызов ClaudeClient.complete(model=MODEL_DRAFTER, ...)"
        )
