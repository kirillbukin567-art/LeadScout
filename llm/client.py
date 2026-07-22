"""Обёртка над Anthropic SDK (ТЗ §8, стек §5).

Скоринг — claude-haiku (дешевле, высокий объём вызовов после триггер-фильтра),
черновики первого сообщения и реплики в диалоге — claude-sonnet (качество текста).

Названия моделей ниже — placeholder, зафиксировать точную версию перед продом
(Anthropic периодически обновляет алиасы моделей).

TODO(этап 1, MVP): реализовать реальный вызов anthropic.Anthropic(...).messages.create(...).
Сетевой код пока не добавлен — это только каркас.
"""

from __future__ import annotations

from core.settings import get_settings

MODEL_SCORER = "claude-haiku-4-5"  # TODO: зафиксировать точную версию модели
MODEL_DRAFTER = "claude-sonnet-4-5"  # TODO: зафиксировать точную версию модели


class ClaudeClient:
    """Ленивая обёртка над anthropic.Anthropic — клиент создаётся при первом вызове,
    чтобы импорт модуля не требовал наличия ключа/сети."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().anthropic_api_key
        self._client = None  # type: ignore[var-annotated]

    def _ensure_client(self):
        if self._client is None:
            import anthropic  # локальный импорт — не тянуть SDK, если клиент не используется

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 1024,
    ) -> str:
        """Возвращает текст ответа модели. Реализация — этап 1/2 (MVP)."""

        raise NotImplementedError(
            "TODO: вызов self._ensure_client().messages.create(model=model, "
            "system=system_prompt, messages=[{'role': 'user', 'content': user_content}], "
            "max_tokens=max_tokens) и извлечение текста из ответа"
        )
