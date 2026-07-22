# LeadScout

Мультиагентный ИИ-бот поиска и первичного контакта лидов для партнёрской
программы BingX. Полное техническое задание — [`TZ_LeadScout_Bot.md`](TZ_LeadScout_Bot.md)
(версия 1.2), краткое описание — [`LeadScout_Brief.md`](LeadScout_Brief.md).

> **Статус:** каркас проекта (структура, модели данных, конфиги, интерфейсы).
> Сетевые вызовы (Telethon/aiogram/PRAW/YouTube/VK/Anthropic) — не реализованы,
> помечены `NotImplementedError` с `TODO` и ссылкой на раздел ТЗ.

## Жёсткие правила (не отключаются конфигом)

- Холодные сообщения отправляются только после Approve оператора — полной
  автономной рассылки в системе нет by design (§2.1 ТЗ).
- Rate limits на отправку (§10 ТЗ) — реализуются в коде, без флага отключения.
- Реферальная ссылка никогда не публикуется в открытых сообщениях/комментариях.
- Все секреты — только из `.env`, никогда в коде.

## Структура проекта

```
connectors/     — коннекторы источников (Telegram/Reddit/YouTube/VK/generic), единый интерфейс SourceConnector
core/           — модели БД, настройки, триггер-фильтр, rate limiter, БД-сессии
llm/            — обёртка над Anthropic SDK, JSON-парсинг с retry, промпты (llm/prompts/*.md)
agents/         — оркестрация: Monitor, Scout, Scorer, Drafter, Replier (§16 — мультиагентность)
controlbot/     — управляющий Telegram-бот (aiogram): команды, кнопки, клавиатуры
config/         — sources.yaml, triggers.yaml, geo.yaml, limits.yaml
knowledge/      — bingx_facts.md — база знаний для диалогов (заполняет заказчик)
data/           — SQLite БД (data/leadscout.db), в git не попадает
scripts/        — init_db.py, seed_sources.py
tests/          — pytest: триггер-фильтр, rate limiter, парсинг JSON от LLM
```

## Установка

Требуется Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -e .
```

Скопируйте файл окружения и заполните секреты (см. пояснения в файле, §11 ТЗ):

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

## Запуск

Инициализировать БД (создаёт `data/leadscout.db` по моделям `core/models.py`):

```bash
python -m scripts.init_db
```

Загрузить стартовый реестр источников из `config/sources.yaml` (только при
первом запуске — далее реестр живёт в БД, см. §16 ТЗ):

```bash
python -m scripts.seed_sources
```

Запустить управляющего Telegram-бота (после реализации сетевого слоя):

```bash
python -m controlbot.bot
```

## Тесты

```bash
pytest
```

Покрывают: триггер-фильтр (`core/trigger_filter.py`), анти-бан rate limiter
(`core/rate_limiter.py`, включая проверку, что конфиг не ослабляет лимиты §10),
строгий парсинг JSON-ответов LLM с retry (`llm/json_utils.py`).

## Конфигурация

| Файл | Назначение |
|---|---|
| `.env` | секреты (ключи API, токены, ID) — см. `.env.example`, §11 ТЗ |
| `config/sources.yaml` | стартовый seed реестра источников по платформам |
| `config/triggers.yaml` | словари триггер-фильтра RU/EN/ES/FR (§7, §18 ТЗ) |
| `config/geo.yaml` | allowed/blocked/high_risk/cards_restricted страны (§1, §11 ТЗ) |
| `config/limits.yaml` | анти-бан лимиты отправки (§10 ТЗ), только в сторону ужесточения |
| `knowledge/bingx_facts.md` | база знаний для диалогов — заполняет заказчик (§18 ТЗ) |
| `llm/prompts/*.md` | системные промпты LLM — заказчик итерирует без участия разработчика |

## Следующие шаги реализации (по этапам ТЗ §13)

1. **MVP:** сетевой слой `connectors/telegram_connector.py` + `reddit_connector.py`,
   `llm/client.py` (реальный вызов Anthropic), `agents/monitor.py` + `agents/scorer.py`,
   режим M1 (карточки без отправки).
2. **Этап 2:** Sender через Telethon, Approve-кнопки в `controlbot/handlers.py`,
   `agents/drafter.py` + `agents/replier.py`, применение `core/rate_limiter.py`.
3. **Этап 3:** YouTube/VK/`generic_parser.py`, `agents/scout.py` (Discovery),
   `/stats`, `/export`, feedback-цикл словарей (§18).
4. **Этап 4 (v2):** автодиалог M3, Discord Bot API, X API, языки PT/AR (§15).
