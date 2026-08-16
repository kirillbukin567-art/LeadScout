"""Первичная авторизация мониторинговой Telegram-сессии (TG_SESSION_MONITOR, §10, §11 ТЗ).

Разовая интерактивная процедура: Telethon запросит номер телефона, код из
Telegram и (если включена) пароль двухфакторной аутентификации, после чего
сохранит файл сессии `<TG_SESSION_MONITOR>.session` — дальше `scripts/run_monitor.py`
использует его без повторного логина.

Мониторинговый аккаунт — только для чтения (§10 ТЗ): здесь не выполняется
ни отправка сообщений, ни вступление в чаты, только авторизация клиента.

Запуск:
    python -m scripts.login_monitor
"""

from __future__ import annotations

from loguru import logger
from telethon import TelegramClient

from core.settings import get_settings


def main() -> None:
    settings = get_settings()
    client = TelegramClient(
        settings.tg_session_monitor, settings.tg_api_id, settings.tg_api_hash
    )

    # Синхронный запуск: Telethon сам проведёт диалог (телефон/код/пароль 2FA)
    # через input(), если сессия ещё не авторизована.
    client.start()
    try:
        me = client.get_me()
        logger.info(
            "Сессия '{}' авторизована: {} (id={}). Файл сессии сохранён, "
            "теперь можно запускать python -m scripts.run_monitor",
            settings.tg_session_monitor,
            getattr(me, "username", None) or getattr(me, "first_name", ""),
            me.id,
        )
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
