"""Настройка SQLAlchemy engine/session (SQLite, файл data/leadscout.db, §6 ТЗ).

Никакой сетевой логики здесь нет — только локальная БД. Подключение к
Postgres при росте нагрузки делается заменой DATABASE_URL в .env, без
изменения кода благодаря SQLAlchemy.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.models import Base
from core.settings import get_settings

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Возвращает singleton engine, создавая его при первом обращении."""

    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
        logger.info("SQLAlchemy engine создан: {}", settings.database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Контекстный менеджер сессии с автоматическим commit/rollback."""

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Создаёт все таблицы, описанные в core/models.py (используется в scripts/init_db.py)."""

    Base.metadata.create_all(bind=get_engine())
    logger.info("Схема БД создана/проверена")
