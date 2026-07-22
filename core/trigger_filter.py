"""Триггер-фильтр уровня 1, без LLM (ТЗ §7).

Отсекает ~90–95% потока сообщений до обращения к дорогому LLM Scorer.
Словари живут в config/triggers.yaml (RU/EN/ES/FR), развиваются командами
управляющего бота (/dict add|del|list, §18) — сюда попадают уже как
готовый dict через TriggerFilter.from_yaml().

Категории (см. §7):
    pain_exchange    — боль по текущей бирже
    activity         — признаки активной торговли
    partner_signals  — признаки потенциального субпартнёра
    anti_triggers     — спам/airdrop/казино — сразу filtered_out
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_TRIGGERS_PATH = CONFIG_DIR / "triggers.yaml"

ANTI_TRIGGER_CATEGORY = "anti_triggers"
CANDIDATE_CATEGORIES = ("pain_exchange", "activity", "partner_signals")


class TriggerHit(BaseModel):
    """Одно совпадение фразы словаря в тексте сообщения."""

    category: str
    phrase: str


class TriggerFilterResult(BaseModel):
    """Результат прогона сообщения через триггер-фильтр."""

    lang: str
    hits: list[TriggerHit] = []
    is_anti_trigger: bool = False

    @property
    def is_candidate(self) -> bool:
        """Кандидат идёт дальше в LLM Scorer, если есть «хорошие» триггеры
        и нет анти-триггеров (спам/airdrop перебивает любые совпадения)."""

        if self.is_anti_trigger:
            return False
        return any(hit.category in CANDIDATE_CATEGORIES for hit in self.hits)


class TriggerFilter:
    """Простой substring-матчер словарей триггеров по языкам и категориям."""

    def __init__(self, triggers: dict[str, dict[str, list[str]]]) -> None:
        self._triggers = triggers

    @classmethod
    def from_yaml(cls, path: Path | str = DEFAULT_TRIGGERS_PATH) -> "TriggerFilter":
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(data)

    def check(self, text: str, lang: str) -> TriggerFilterResult:
        """Ищет совпадения словаря языка `lang` в `text` (без учёта регистра).

        Если словаря для языка нет — возвращает пустой результат (не кандидат),
        а не ошибку: неизвестный язык не должен ронять конвейер Ingest.
        """

        categories = self._triggers.get(lang, {})
        text_lower = text.lower()
        hits: list[TriggerHit] = []
        for category, phrases in categories.items():
            for phrase in phrases:
                if phrase.lower() in text_lower:
                    hits.append(TriggerHit(category=category, phrase=phrase))

        is_anti = any(hit.category == ANTI_TRIGGER_CATEGORY for hit in hits)
        return TriggerFilterResult(lang=lang, hits=hits, is_anti_trigger=is_anti)
