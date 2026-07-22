"""Универсальный парсер сайтов без API (ТЗ §17) — форумы, доски объявлений,
региональные сайты.

Дисциплина парсинга (обязательна к реализации, не опция):
    - уважение robots.txt;
    - интервал ≥ 30 сек между запросами к одному домену;
    - кастомный User-Agent;
    - кэширование уже обработанных страниц;
    - автостоп при HTTP 403/429 с алертом оператору;
    - RSS-first: если у ресурса есть RSS — использовать его вместо HTML-парсинга.

Статичные страницы — requests + BeautifulSoup. JS-сайты — Playwright
(headless Chromium), включается флагом `render_js` в конфиге источника,
используется точечно (тяжелее по ресурсам VPS).

НЕ покрывает: X, Instagram, Facebook, LinkedIn (антибот, требует логина —
риск бана аккаунта). TradingView — допустим на минимальной частоте
(1 запрос/мин, только публичные URL Ideas).

TODO(этап 3, v1.1): реализовать сетевой слой (requests/BeautifulSoup,
опционально Playwright). Сетевой код пока не добавлен — это только каркас.
"""

from __future__ import annotations

from pydantic import BaseModel

from connectors.base import RawMessage, SourceConnector


class GenericParserSelectors(BaseModel):
    """CSS-селекторы контейнера поста и его полей — хранятся в конфиге
    источника (БД, изначально seed из config/sources.yaml), новый сайт
    подключается записью конфига, без изменения кода."""

    post_container: str
    author: str
    text: str
    date: str
    link: str


class GenericParserConnector(SourceConnector):
    """Универсальный HTTP-парсер (requests+BeautifulSoup, опционально Playwright)."""

    platform = "generic"

    def poll(self) -> list[RawMessage]:
        raise NotImplementedError(
            "TODO: реализовать requests+BeautifulSoup (и Playwright при render_js=True), "
            "с соблюдением robots.txt, интервалов и RSS-first (§17)"
        )
