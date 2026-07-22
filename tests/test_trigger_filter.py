"""Тесты триггер-фильтра уровня 1 (ТЗ §7).

Два блока:
1. Тесты на изолированном SAMPLE_TRIGGERS — проверяют логику TriggerFilter
   независимо от содержимого боевого словаря.
2. Тесты на реальном config/triggers.yaml (через TriggerFilter.from_yaml()) —
   проверяют, что боевые словари RU/EN/ES/FR реально ловят типичные сообщения
   по всем категориям и не ловят нейтральные/похожие-но-не-триггерные тексты
   (ложные срабатывания).
"""

import pytest

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


# --- Блок 1: логика фильтра на изолированном словаре -----------------------


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


# --- Блок 2: боевой словарь config/triggers.yaml (RU/EN/ES/FR) -------------


@pytest.fixture(scope="module")
def real_filter() -> TriggerFilter:
    return TriggerFilter.from_yaml()


# Каждый кейс: (lang, text, ожидаемая категория среди hits)
PAIN_CASES = [
    ("ru", "На этой бирже комиссия огромная, третий день завис вывод", "pain_exchange"),
    ("ru", "Задумался, куда уйти с биржи — какую биржу выбрать для фьючерсов", "pain_exchange"),
    ("en", "High exchange fees are ridiculous, and my withdrawal stuck for a week", "pain_exchange"),
    ("en", "Anyone knows the best low fee exchange? Thinking about switching from binance", "pain_exchange"),
    ("es", "Las comisiones altas me tienen loco, no puedo retirar mis fondos", "pain_exchange"),
    ("es", "Busco cuál es mejor exchange para futuros, cansado de binance", "pain_exchange"),
    ("fr", "Les frais trop élevés sont un scandale, et mon retrait bloqué depuis 3 jours", "pain_exchange"),
    ("fr", "Je cherche la meilleure plateforme trading, marre des frais de bybit", "pain_exchange"),
]

ACTIVITY_CASES = [
    ("ru", "Взял лонг с плечом x20 на фьючерсах, жду funding rate", "activity"),
    ("ru", "Меня ликвидировали на bybit, показываю скрин моего pnl", "activity"),
    ("en", "Went long with leverage x10 on futures, got liquidated at the worst time", "activity"),
    ("en", "Switched from bybit to okx, trading futures with margin trading now", "activity"),
    ("es", "Entré en corto con apalancamiento x20 en futuros y me liquidaron", "activity"),
    ("es", "Hago scalping en binance, mi pnl de hoy fue positivo", "activity"),
    ("fr", "J'ai pris du long avec un effet de levier x10 sur les futures", "activity"),
    ("fr", "J'ai été liquidé sur bybit, mon pnl du jour est catastrophique", "activity"),
]

PARTNER_CASES = [
    ("ru", "Веду крипто-канал, хочу монетизировать канал и ищу партнёрку", "partner_signals"),
    ("en", "I run a trading channel and I'm looking for affiliate program", "partner_signals"),
    ("es", "Tengo un canal de trading y busco programa de afiliados", "partner_signals"),
    ("fr", "J'ai une chaîne de trading et je cherche un programme d'affiliation", "partner_signals"),
]

ANTI_CASES = [
    ("ru", "Заходи в бота, там раздача монет и казино с бонусами", "anti_triggers"),
    ("en", "Join my bot for a free airdrop giveaway, also check our casino bonus", "anti_triggers"),
    ("es", "Únete a mi bot, hay un sorteo y bono de casino para todos", "anti_triggers"),
    ("fr", "Rejoins mon bot, il y a un tirage au sort et un bonus casino", "anti_triggers"),
]


@pytest.mark.parametrize(("lang", "text", "expected_category"), PAIN_CASES)
def test_pain_exchange_real_dict(real_filter, lang, text, expected_category) -> None:
    result = real_filter.check(text, lang)
    categories = {hit.category for hit in result.hits}
    assert expected_category in categories
    assert result.is_candidate


@pytest.mark.parametrize(("lang", "text", "expected_category"), ACTIVITY_CASES)
def test_activity_real_dict(real_filter, lang, text, expected_category) -> None:
    result = real_filter.check(text, lang)
    categories = {hit.category for hit in result.hits}
    assert expected_category in categories
    assert result.is_candidate


@pytest.mark.parametrize(("lang", "text", "expected_category"), PARTNER_CASES)
def test_partner_signals_real_dict(real_filter, lang, text, expected_category) -> None:
    result = real_filter.check(text, lang)
    categories = {hit.category for hit in result.hits}
    assert expected_category in categories
    assert result.is_candidate


@pytest.mark.parametrize(("lang", "text", "expected_category"), ANTI_CASES)
def test_anti_triggers_real_dict(real_filter, lang, text, expected_category) -> None:
    result = real_filter.check(text, lang)
    categories = {hit.category for hit in result.hits}
    assert expected_category in categories
    assert result.is_anti_trigger
    assert not result.is_candidate  # анти-триггер перебивает любые «хорошие» совпадения


# --- Ложные срабатывания ----------------------------------------------------

NEUTRAL_CASES = [
    ("ru", "Сегодня хорошая погода, ничего интересного не происходит"),
    ("en", "I'm reading a book about gardening and cooking pasta tonight"),
    ("es", "Hoy hice ejercicio y luego cociné pasta con mis amigos"),
    ("fr", "Aujourd'hui il fait beau et je vais me promener au parc"),
]


@pytest.mark.parametrize(("lang", "text"), NEUTRAL_CASES)
def test_neutral_text_is_not_candidate(real_filter, lang, text) -> None:
    result = real_filter.check(text, lang)
    assert not result.hits
    assert not result.is_candidate


def test_generic_word_funding_alone_does_not_trigger_activity(real_filter) -> None:
    """«funding» само по себе (например, финансирование стартапа) не должно
    ловиться как признак активной торговли — в словаре только фраза
    «funding rate», а не одиночное слово."""

    text = "Our startup just closed a funding round from investors"
    result = real_filter.check(text, "en")
    activity_hits = [hit for hit in result.hits if hit.category == "activity"]
    assert not activity_hits


def test_casino_word_without_gambling_context_does_not_trigger_anti(real_filter) -> None:
    """Слово «casino» само по себе (например, название фильма) не должно
    ловиться анти-триггером — в словаре только «casino bonus»/«online casino»."""

    text = "We watched the movie Casino last night, great soundtrack"
    result = real_filter.check(text, "en")
    assert not result.is_anti_trigger


def test_unrelated_finance_text_does_not_trigger_pain(real_filter) -> None:
    """Обсуждение личных финансов без упоминания бирж/комиссий не должно
    ловиться как боль по бирже."""

    text = "I'm trying to build a monthly budget and save more money"
    result = real_filter.check(text, "en")
    pain_hits = [hit for hit in result.hits if hit.category == "pain_exchange"]
    assert not pain_hits
