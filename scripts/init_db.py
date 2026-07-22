"""Создаёт схему БД (data/leadscout.db) по моделям core/models.py.

Запуск:
    python -m scripts.init_db
"""

from __future__ import annotations

from loguru import logger

from core.db import init_db


def main() -> None:
    init_db()
    logger.info("Готово: схема БД создана/проверена в data/leadscout.db")


if __name__ == "__main__":
    main()
