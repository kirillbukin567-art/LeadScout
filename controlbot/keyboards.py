"""Инлайн-клавиатуры управляющего Telegram-бота (ТЗ §9).

Чистая UI-логика без сети/БД — сборка разметки кнопок aiogram.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def lead_card_keyboard(lead_id: int, profile_url: str | None = None) -> InlineKeyboardMarkup:
    """Кнопки карточки лида: [Отправить] [Редактировать] [Открыть профиль]
    [Пропустить] [Не лид] — пример разметки из §9 ТЗ."""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data=f"lead:send:{lead_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"lead:edit:{lead_id}")
    if profile_url:
        builder.button(text="🌐 Открыть профиль", url=profile_url)
    builder.button(text="⏭ Пропустить", callback_data=f"lead:skip:{lead_id}")
    builder.button(text="🚫 Не лид", callback_data=f"lead:not_lead:{lead_id}")
    builder.adjust(2)
    return builder.as_markup()


def dialogue_reply_keyboard(dialogue_id: int) -> InlineKeyboardMarkup:
    """Кнопки под черновиком реплики в диалоге (§9 ТЗ):
    [Отправить] [Редактировать] [Взять на себя] [🤖 Автопилот (v2)]."""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data=f"dlg:send:{dialogue_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"dlg:edit:{dialogue_id}")
    builder.button(text="🙋 Взять на себя", callback_data=f"dlg:takeover:{dialogue_id}")
    builder.button(text="🤖 Автопилот", callback_data=f"dlg:autopilot:{dialogue_id}")
    builder.adjust(2)
    return builder.as_markup()


def source_candidate_keyboard(source_id: int) -> InlineKeyboardMarkup:
    """Кнопки карточки источника от Scout-агента (§16 ТЗ):
    [Подключить] [Отклонить] [Отложить]."""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подключить", callback_data=f"source:connect:{source_id}")
    builder.button(text="🚫 Отклонить", callback_data=f"source:reject:{source_id}")
    builder.button(text="⏸ Отложить", callback_data=f"source:postpone:{source_id}")
    builder.adjust(3)
    return builder.as_markup()


def dict_suggestion_keyboard(suggestion_id: int) -> InlineKeyboardMarkup:
    """Кнопки автопредложения словаря триггеров (§18 ТЗ): [Добавить] [Отклонить]."""

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить", callback_data=f"dict:accept:{suggestion_id}")
    builder.button(text="🚫 Отклонить", callback_data=f"dict:reject:{suggestion_id}")
    builder.adjust(2)
    return builder.as_markup()
