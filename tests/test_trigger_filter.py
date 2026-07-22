"""Тесты триггер-фильтра уровня 1 (ТЗ §7)."""

from core.trigger_filter import TriggerFilter

SAMPLE_TRIGGERS = {
    "ru": {
        "pain_exchange": ["комиссия огромная", "ищу биржу"],
        "activity": ["плечо x", "фьючерс"],
        "partner_signals": ["монетизировать канал"],
        "anti_triggers": ["раздача", "airdrop"],
    },
    "en": {
        "pain_exchange": ["fees are killing me"],
        "activity": ["leverage x", "futures"],
        "partner_signals": ["monetize my channel"],
        "anti_triggers": ["giveaway"],
    },
}


def make_filter() -> TriggerFilter:
    return TriggerFilter(SAMPLE_TRIGGERS)


def test_pain_trigger_is_candidate() -> None:
    result = make_filter().check("Комиссия огромная на этой бирже, ищу биржу с фьючерсами", "ru")
    assert result.is_candidate
    assert not result.is_anti_trigger
    categories = {hit.category for hit in result.hits}
    assert "pain_exchange" in categories


def test_anti_trigger_overrides_candidate_signal() -> None:
    text = "Комиссия огромная! Забирай airdrop прямо сейчас"
    result = make_filter().check(text, "ru")
    assert result.is_anti_trigger
    assert not result.is_candidate


def test_no_match_is_not_candidate() -> None:
    result = make_filter().check("Какой сегодня хороший день", "ru")
    assert not result.hits
    assert not result.is_candidate


def test_case_insensitive_matching() -> None:
    result = make_filter().check("FEES ARE KILLING ME on this exchange", "en")
    assert result.is_candidate


def test_unknown_language_returns_empty_result() -> None:
    result = make_filter().check("some text", "de")
    assert result.hits == []
    assert not result.is_candidate


def test_from_yaml_loads_real_config() -> None:
    """Проверяем, что реальный config/triggers.yaml валиден и грузится."""

    trigger_filter = TriggerFilter.from_yaml()
    result = trigger_filter.check("fees are killing me on this exchange", "en")
    assert result.is_candidate
