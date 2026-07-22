"""Загружает стартовый реестр источников из config/sources.yaml в таблицу
`sources` (ТЗ §11, §16 — sources.yaml используется только как seed при первом
запуске, дальше реестр живёт в БД и пополняется Scout-агентом/командой /sources).

Идемпотентно: уже существующие записи (platform, handle) не дублируются.

Запуск:
    python -m scripts.seed_sources
"""

from __future__ import annotations

from pathlib import Path

import yaml
from loguru import logger

from core.db import init_db, session_scope
from core.models import DiscoveredBy, Source, SourceStatus

DEFAULT_SOURCES_PATH = Path(__file__).resolve().parent.parent / "config" / "sources.yaml"


def seed_from_yaml(path: Path | str = DEFAULT_SOURCES_PATH) -> int:
    """Читает config/sources.yaml и создаёт недостающие записи Source.

    Возвращает количество созданных записей.
    """

    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    created = 0
    with session_scope() as session:
        for platform, entries in data.items():
            for entry in entries or []:
                handle = entry["handle"]
                already_exists = (
                    session.query(Source)
                    .filter_by(platform=platform, handle=handle)
                    .first()
                    is not None
                )
                if already_exists:
                    continue

                session.add(
                    Source(
                        platform=platform,
                        handle=handle,
                        lang=entry.get("lang", "en"),
                        region=entry.get("region"),
                        enabled=bool(entry.get("enabled", False)),
                        discovered_by=DiscoveredBy.SEED,
                        status=SourceStatus.CANDIDATE,
                    )
                )
                created += 1

    logger.info("Seed-загрузка источников завершена: добавлено {}", created)
    return created


def main() -> None:
    init_db()
    seed_from_yaml()


if __name__ == "__main__":
    main()
