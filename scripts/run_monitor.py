"""Запуск Telegram-монитора (Telethon, только чтение) в реальном времени (ТЗ §4, §5, §10).

Перед первым запуском сессию нужно авторизовать:
    python -m scripts.login_monitor

Дальше монитор сам засеивает реестр источников из config/sources.yaml (если
таблица sources пуста), подписывается на новые сообщения активных Telegram-
источников (status=active) и пишет кандидатов, прошедших триггер-фильтр, в
messages со статусом scored_pending — для последующего LLM Scorer.

Запуск:
    python -m scripts.run_monitor
"""

from __future__ import annotations

import asyncio

from loguru import logger

from connectors.telegram_monitor import TelegramMonitor


async def _main() -> None:
    monitor = TelegramMonitor()
    await monitor.start()


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Telegram-монитор остановлен оператором (Ctrl+C)")


if __name__ == "__main__":
    main()
