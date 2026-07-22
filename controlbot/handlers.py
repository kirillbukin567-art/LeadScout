"""Хендлеры команд и callback-кнопок управляющего Telegram-бота (ТЗ §9, §12, §16, §18).

Доступ только оператору (settings.operator_tg_id) — проверка должна стоять на
уровне middleware/фильтра при подключении router в controlbot/bot.py.

TODO(этап 1-4, по разделам): реализовать тела хендлеров (чтение/запись БД,
вызов агентов из agents/). Сетевой код (сама отправка сообщений через
Telethon-Sender) находится вне controlbot — здесь только интерфейс оператора.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router(name="leadscout-control")


# --------------------------------------------------------------------------- #
# Команды (§9 ТЗ)
# --------------------------------------------------------------------------- #


@router.message(Command("mode"))
async def cmd_mode(message: Message) -> None:
    """`/mode m1|m2` — переключение режима работы (M3 включается только в
    карточке конкретного диалога, не этой командой, см. §3)."""

    raise NotImplementedError("TODO: разобрать аргумент, записать SettingRecord(key='mode', ...)")


@router.message(Command("threshold"))
async def cmd_threshold(message: Message) -> None:
    """`/threshold N` — порог score для отправки карточки оператору (§8.1)."""

    raise NotImplementedError("TODO: валидировать 0..100, записать SettingRecord")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """`/stats [7d|30d]` — воронка по метрикам §12."""

    raise NotImplementedError("TODO: агрегация по leads/outreach/dialogues за период")


@router.message(Command("queue"))
async def cmd_queue(message: Message) -> None:
    """`/queue` — очередь отправки (approved, ожидающие Sender)."""

    raise NotImplementedError("TODO: список Lead.state == approved")


@router.message(Command("dialogues"))
async def cmd_dialogues(message: Message) -> None:
    """`/dialogues` — активные диалоги, вход в любой."""

    raise NotImplementedError("TODO: список активных Dialogue")


@router.message(Command("pause"))
async def cmd_pause(message: Message) -> None:
    """`/pause` — полная пауза отправки (например по FloodWait, §10)."""

    raise NotImplementedError("TODO: SettingRecord(key='sending_paused', value='true')")


@router.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
    """`/resume` — снятие паузы отправки."""

    raise NotImplementedError("TODO: SettingRecord(key='sending_paused', value='false')")


@router.message(Command("sources"))
async def cmd_sources(message: Message) -> None:
    """`/sources` — включение/выключение источников мониторинга."""

    raise NotImplementedError("TODO: список Source + кнопки toggle enabled")


@router.message(Command("manual"))
async def cmd_manual(message: Message) -> None:
    """`/manual <url или текст>` — ручное создание карточки (Instagram/FB и т.п., §4)."""

    raise NotImplementedError("TODO: создать Message(status=lead-candidate) вручную + запустить Scorer")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """`/export` — CSV-экспорт лидов (§9, §12)."""

    raise NotImplementedError("TODO: выгрузка leads в CSV и отправка файлом")


@router.message(Command("discover"))
async def cmd_discover(message: Message) -> None:
    """`/discover <регион|язык|тема>` — ручной запуск Scout-агента (§16)."""

    raise NotImplementedError("TODO: agents.scout.ScoutAgent.discover(...)")


@router.message(Command("converted"))
async def cmd_converted(message: Message) -> None:
    """`/converted <id> <stage>` — ручная отметка пост-регистрационной стадии
    воронки (registered|cashback_set|funded|active), сверка с кабинетом BingX (§12)."""

    raise NotImplementedError("TODO: обновить Lead.state по id, валидировать допустимый stage")


@router.message(Command("dict"))
async def cmd_dict(message: Message) -> None:
    """`/dict add|del|list <lang> <категория> <фраза>` — развитие словарей
    триггеров без участия разработчика, версионируется в dict_history (§18)."""

    raise NotImplementedError("TODO: разбор подкоманды add/del/list + запись DictHistory")


# --------------------------------------------------------------------------- #
# Callback-кнопки карточек (§9, §16, §18 ТЗ)
# --------------------------------------------------------------------------- #


@router.callback_query(F.data.startswith("lead:"))
async def on_lead_action(callback: CallbackQuery) -> None:
    """Кнопки карточки лида: send (Approve) | edit | skip | not_lead.

    `not_lead` обязательно пишет запись в Feedback (§9) — для донастройки
    промпта скоринга."""

    raise NotImplementedError("TODO: разобрать callback.data, ветвление по действию")


@router.callback_query(F.data.startswith("dlg:"))
async def on_dialogue_action(callback: CallbackQuery) -> None:
    """Кнопки диалога: send | edit | takeover | autopilot (M3, per-dialogue, v2)."""

    raise NotImplementedError("TODO: разобрать callback.data, ветвление по действию")


@router.callback_query(F.data.startswith("source:"))
async def on_source_candidate_action(callback: CallbackQuery) -> None:
    """Кнопки карточки источника от Scout-агента: connect | reject | postpone (§16)."""

    raise NotImplementedError("TODO: обновить Source.status по действию")


@router.callback_query(F.data.startswith("dict:"))
async def on_dict_suggestion_action(callback: CallbackQuery) -> None:
    """Кнопки автопредложения словаря: accept | reject (§18)."""

    raise NotImplementedError("TODO: применить/отклонить предложение, записать DictHistory")
