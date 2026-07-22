"""Точка входа управляющего Telegram-бота (aiogram 3, ТЗ §9).

Единственное место, где интерфейс оператора «оживает». Сама отправка бота на
polling — только внутри `if __name__ == "__main__"`, импорт модуля не делает
сетевых вызовов (важно для тестов и для сборки каркаса без сети).
"""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from controlbot.handlers import router
from core.settings import get_settings


def build_dispatcher() -> Dispatcher:
    """Собирает Dispatcher с зарегистрированными роутерами (без запуска polling)."""

    dp = Dispatcher()
    dp.include_router(router)
    return dp


def build_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.control_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def _run() -> None:
    bot = build_bot()
    dp = build_dispatcher()
    logger.info("Управляющий бот запускается (long polling)")
    # TODO: здесь же поднять APScheduler для утреннего дайджеста (§12) и
    # периодических задач Monitor/Scout-агентов (§16), см. agents/.
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
