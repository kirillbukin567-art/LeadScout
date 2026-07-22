"""LLM Scorer — классификация, скоринг и извлечение фактов (ТЗ §8.1).

Один вызов Claude Haiku на кандидата, прошедшего триггер-фильтр
(core/trigger_filter.py). Системный промпт — llm/prompts/scoring_system.md.

TODO(этап 1, MVP): собрать user-контент (текст сообщения + метаданные:
площадка, чат, язык, до 5 предыдущих сообщений автора), вызвать
llm.client.ClaudeClient, распарсить через llm.json_utils.call_llm_json и
провалидировать llm.schemas.ScoringResult.
"""

from __future__ import annotations

from pathlib import Path

from llm.client import ClaudeClient, MODEL_SCORER
from llm.schemas import ScoringResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SCORING_SYSTEM_PROMPT_PATH = PROMPTS_DIR / "scoring_system.md"


class Scorer:
    """Обёртка над LLM-вызовом скоринга кандидата."""

    def __init__(self, client: ClaudeClient | None = None) -> None:
        self.client = client or ClaudeClient()

    def score(self, message_text: str, meta: dict) -> ScoringResult:
        """meta: {"platform": ..., "chat": ..., "lang": ..., "author_history": [...]}"""

        raise NotImplementedError(
            "TODO: system_prompt = SCORING_SYSTEM_PROMPT_PATH.read_text(); "
            "вызов ClaudeClient.complete(model=MODEL_SCORER, ...); "
            "call_llm_json + ScoringResult.model_validate"
        )
