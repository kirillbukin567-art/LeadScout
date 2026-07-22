"""Pydantic-схемы строгих JSON-контрактов LLM-слоя (ТЗ §8.1).

Используются для валидации ответа после llm/json_utils.call_llm_json —
если Claude вернёт JSON с неверными типами/отсутствующими полями,
pydantic поднимет ValidationError, что тоже должно уходить в retry-цикл
вызывающего кода (см. llm/scorer.py).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScoringFacts(BaseModel):
    """Извлечённые факты о лиде (§8.1 — пример: exchange/instruments/pain)."""

    current_exchange: str | None = None
    instruments: list[str] = Field(default_factory=list)
    pain: str | None = None

    class Config:
        extra = "allow"  # LLM может прислать доп. факты, не теряем их


class ScoringResult(BaseModel):
    """Строгий JSON-ответ LLM Scorer (пример в §8.1 ТЗ)."""

    is_lead: bool
    lead_type: Literal["trader", "partner"]
    score: int = Field(ge=0, le=100)
    lang: str
    reasons: list[str]
    facts: ScoringFacts
    geo_hint: str | None = None
    recommended_angle: str
    recommended_method: Literal["pain_catch", "helpful_reply", "warm_intro", "partner_pitch"]


class DialogueReplyResult(BaseModel):
    """Ответ LLM Replier (§8.3): основная реплика + альтернатива."""

    reply: str
    alternative_reply: str
    escalate: bool = False
    escalation_reason: str | None = None
