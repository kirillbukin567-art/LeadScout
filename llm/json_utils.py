"""Строгий парсинг JSON-ответов LLM с retry (правило проекта: до 2 повторов
при невалидном ответе; ТЗ §8.1 — выход LLM Scorer строго JSON).

Чистая логика, без сетевых вызовов — сама функция генерации ответа (`generate`)
передаётся вызывающим кодом (llm/scorer.py, llm/drafter.py), что делает этот
модуль легко тестируемым без реального обращения к Anthropic API.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from loguru import logger

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMJsonParseError(Exception):
    """Ответ LLM не удалось распарсить как валидный JSON."""


def _strip_code_fences(raw: str) -> str:
    """Claude иногда оборачивает JSON в ```json ... ``` — убираем обёртку."""

    return _CODE_FENCE_RE.sub("", raw.strip()).strip()


def parse_llm_json(raw: str) -> dict[str, Any]:
    """Парсит строку ответа LLM как JSON-объект.

    Поднимает LLMJsonParseError с понятным сообщением при любой ошибке —
    невалидный JSON, JSON-массив/скаляр вместо объекта и т.п.
    """

    cleaned = _strip_code_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMJsonParseError(f"Невалидный JSON от LLM: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMJsonParseError(f"Ожидался JSON-объект, получено: {type(data).__name__}")

    return data


def call_llm_json(
    generate: Callable[[int], str],
    max_retries: int = 2,
) -> dict[str, Any]:
    """Вызывает `generate(attempt)` и парсит результат как JSON.

    При невалидном ответе повторяет вызов до `max_retries` раз (итого до
    max_retries + 1 попыток), как требует регламент проекта. `generate`
    получает номер попытки (с нуля) — можно использовать, чтобы добавить в
    промпт подсказку «предыдущий ответ был не валиден» на повторных попытках.
    """

    last_error: LLMJsonParseError | None = None
    for attempt in range(max_retries + 1):
        raw = generate(attempt)
        try:
            return parse_llm_json(raw)
        except LLMJsonParseError as exc:
            last_error = exc
            logger.warning("Попытка {}/{}: {}", attempt + 1, max_retries + 1, exc)

    assert last_error is not None
    raise last_error
