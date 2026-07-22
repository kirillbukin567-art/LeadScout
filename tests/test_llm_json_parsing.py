"""Тесты строгого парсинга JSON от LLM с retry (правило проекта: до 2 повторов)."""

import pytest

from llm.json_utils import LLMJsonParseError, call_llm_json, parse_llm_json


def test_parse_plain_json() -> None:
    result = parse_llm_json('{"is_lead": true, "score": 78}')
    assert result == {"is_lead": True, "score": 78}


def test_parse_json_wrapped_in_code_fence() -> None:
    raw = '```json\n{"is_lead": true, "score": 78}\n```'
    result = parse_llm_json(raw)
    assert result == {"is_lead": True, "score": 78}


def test_parse_invalid_json_raises() -> None:
    with pytest.raises(LLMJsonParseError):
        parse_llm_json("это не json вовсе")


def test_parse_json_array_raises() -> None:
    with pytest.raises(LLMJsonParseError):
        parse_llm_json("[1, 2, 3]")


def test_call_llm_json_succeeds_on_first_try() -> None:
    calls = []

    def generate(attempt: int) -> str:
        calls.append(attempt)
        return '{"score": 55}'

    result = call_llm_json(generate, max_retries=2)
    assert result == {"score": 55}
    assert calls == [0]


def test_call_llm_json_retries_then_succeeds() -> None:
    responses = ["не json", "снова не json", '{"score": 90}']

    def generate(attempt: int) -> str:
        return responses[attempt]

    result = call_llm_json(generate, max_retries=2)
    assert result == {"score": 90}


def test_call_llm_json_raises_after_exhausting_retries() -> None:
    def generate(attempt: int) -> str:
        return "всегда невалидный ответ"

    with pytest.raises(LLMJsonParseError):
        call_llm_json(generate, max_retries=2)
