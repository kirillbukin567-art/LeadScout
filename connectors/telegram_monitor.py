"""Telegram-монитор (Telethon, MTProto) — потоковый сбор сообщений (ТЗ §4, §5, §7, §10).

В отличие от опросных коннекторов (Reddit/YouTube/VK), Telegram-мониторинг
работает в реальном времени поверх `events.NewMessage`, поэтому логика ingest
(дедуп + триггер-фильтр + запись в БД) реализована прямо здесь, а не в
`agents/monitor.py` (тот рассчитан на poll-коннекторы `SourceConnector.poll()`).

Жёсткие ограничения (§10 ТЗ):
    - Мониторинговый аккаунт — ТОЛЬКО чтение. Здесь нет ни одного вызова на
      отправку сообщений и ни одного вызова на вступление в чат (вступление —
      вручную, ≤ 2 новых чата/день, вне этого модуля).
    - Запросы к БД — без SQL join'ов: сначала читаем реестр `sources` отдельным
      запросом, затем работаем с `messages` по одному сообщению за раз.

Пайплайн на каждое новое сообщение:
    Telethon NewMessage → RawMessage (нормализация) → дедуп по
    (source_id, ext_id) → TriggerFilter.check() → Message.status:
        - анти-триггер или нет кандидатных триггеров → filtered_out
        - есть кандидатные триггеры и нет анти-триггера → scored_pending
          (кандидат ставится в очередь LLM Scorer, см. agents/scorer.py)

Авторизация сессии — отдельным скриптом `scripts/login_monitor.py` (в этом
модуле интерактивного логина нет). Запуск потока — `scripts/run_monitor.py`.
"""

from __future__ import annotations

import asyncio
from datetime import timezone

from loguru import logger
from sqlalchemy.exc import IntegrityError
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message as TelethonMessage
from telethon.utils import get_peer_id

from connectors.base import RawMessage
from core.db import init_db, session_scope
from core.models import Message, MessageStatus, Source, SourceStatus
from core.settings import get_settings
from core.trigger_filter import TriggerFilter
from scripts.seed_sources import seed_from_yaml

PLATFORM = "telegram"


class TelegramMonitor:
    """Потоковый монитор Telegram-источников — только чтение, без отправок.

    Подписывается на `events.NewMessage` в чатах из реестра `sources`
    (platform="telegram", status="active"). Клиент должен быть уже вручную
    добавлен в эти чаты — модуль не вступает в чаты сам (§10 ТЗ).
    """

    platform = PLATFORM

    def __init__(self, trigger_filter: TriggerFilter | None = None) -> None:
        settings = get_settings()
        self.trigger_filter = trigger_filter or TriggerFilter.from_yaml()
        self.client = TelegramClient(
            settings.tg_session_monitor, settings.tg_api_id, settings.tg_api_hash
        )
        # Соответствие Telethon chat_id -> запись Source, заполняется в start().
        self._source_by_chat_id: dict[int, Source] = {}

    # ------------------------------------------------------------------ #
    # Запуск и подписка
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """Подключается только для чтения, засеивает реестр источников при
        первом запуске, подписывается на новые сообщения активных Telegram-
        источников и слушает поток до отключения."""

        init_db()
        self._ensure_seeded()

        await self.client.start()  # type: ignore[func-returns-value]
        me = await self.client.get_me()
        logger.info(
            "Telegram-монитор подключён как {} (id={}), режим только чтение",
            getattr(me, "username", None) or getattr(me, "first_name", ""),
            me.id,
        )

        # Прогреваем кэш сущностей диалогов клиента — без этого get_entity() по
        # числовому id чата, в который клиент уже вступил вручную, может не
        # резолвиться. Сам по себе get_dialogs() — вызов на чтение, не вступление.
        await self.client.get_dialogs()

        sources = self._load_active_sources()
        if not sources:
            logger.warning(
                "Нет активных Telegram-источников (platform=telegram, status=active) — "
                "монитору нечего слушать. Включите источники через /sources."
            )
            return

        chats = []
        resolved_handles: list[str] = []
        for source in sources:
            entity = await self._resolve_entity(source)
            if entity is None:
                continue
            # ВАЖНО: entity.id — «голый» ID сущности, а event.chat_id в обработчике
            # ниже — «маркированный» ID (для каналов/супергрупп — с префиксом -100,
            # для обычных групп — с минусом). Ключ словаря обязан быть в том же
            # маркированном формате, иначе _on_new_message никогда не найдёт source
            # и все сообщения будут молча отбрасываться.
            self._source_by_chat_id[get_peer_id(entity)] = source
            chats.append(entity)
            resolved_handles.append(source.handle)

        if not chats:
            logger.warning("Ни один активный Telegram-источник не удалось разрешить в сущность")
            return

        self.client.add_event_handler(self._on_new_message, events.NewMessage(chats=chats))
        logger.info(
            "Telegram-монитор слушает {} чат(ов): {}",
            len(chats),
            ", ".join(resolved_handles),
        )

        await self.client.run_until_disconnected()

    def _ensure_seeded(self) -> None:
        """При полностью пустой таблице `sources` засеивает её из
        `config/sources.yaml` (§11, §16 — yaml используется только как
        стартовый seed при первом запуске, дальше реестр живёт в БД)."""

        with session_scope() as session:
            has_any_source = session.query(Source).first() is not None

        if has_any_source:
            return

        logger.info("Таблица sources пуста — выполняю первичный seed из config/sources.yaml")
        seed_from_yaml()

    def _load_active_sources(self) -> list[Source]:
        """Отдельный запрос без join'ов: только сама таблица sources."""

        with session_scope() as session:
            sources = (
                session.query(Source)
                .filter(
                    Source.platform == self.platform,
                    Source.status == SourceStatus.ACTIVE,
                )
                .all()
            )
            session.expunge_all()
            return sources

    async def _resolve_entity(self, source: Source):
        """Возвращает Telethon-сущность чата по `handle` источника.

        Только чтение метаданных (ResolveUsername/GetEntity) — клиент должен
        уже состоять в чате (вступление туда — ручное действие вне монитора,
        §10 ТЗ). Ошибки резолва не должны ронять весь монитор.
        """

        handle = source.handle
        try:
            entity_ref: int | str = int(handle) if _is_int_like(handle) else handle
            return await self.client.get_entity(entity_ref)
        except Exception as exc:  # noqa: BLE001 — резолв не должен ронять монитор целиком
            logger.warning("Не удалось разрешить Telegram-источник '{}': {}", handle, exc)
            return None

    # ------------------------------------------------------------------ #
    # Обработка входящих событий
    # ------------------------------------------------------------------ #

    async def _on_new_message(self, event: events.NewMessage.Event) -> None:
        source = self._source_by_chat_id.get(event.chat_id)
        if source is None:
            return  # сообщение из чата вне реестра активных источников

        raw = await self._to_raw_message(event, source)
        if raw is None:
            return

        self._ingest(raw, source)

    async def _to_raw_message(
        self, event: events.NewMessage.Event, source: Source
    ) -> RawMessage | None:
        """Нормализует событие Telethon в унифицированный RawMessage (§5 ТЗ)."""

        message: TelethonMessage = event.message
        text = (message.raw_text or "").strip()
        if not text:
            return None  # медиа без подписи и т.п. — нечего скорить триггер-фильтром

        sender = await event.get_sender()
        author_ext_id = str(sender.id) if sender is not None else None
        author_handle = getattr(sender, "username", None) if sender is not None else None

        posted_at = message.date
        if posted_at is not None and posted_at.tzinfo is not None:
            posted_at = posted_at.astimezone(timezone.utc).replace(tzinfo=None)

        return RawMessage(
            platform=self.platform,
            source_handle=source.handle,
            ext_id=str(message.id),
            author_ext_id=author_ext_id,
            author_handle=author_handle,
            url=_build_message_url(source.handle, message.id),
            text=text,
            lang=source.lang,
            posted_at=posted_at,
        )

    def _ingest(self, raw: RawMessage, source: Source) -> None:
        """Дедуп по (source_id, ext_id) + триггер-фильтр (§7) + запись в
        `messages`. Кандидаты без анти-триггеров помечаются `scored_pending`."""

        result = self.trigger_filter.check(raw.text, lang=raw.lang or source.lang)
        status = MessageStatus.SCORED_PENDING if result.is_candidate else MessageStatus.FILTERED_OUT
        trigger_hits = ",".join(f"{hit.category}:{hit.phrase}" for hit in result.hits) or None

        with session_scope() as session:
            already_exists = (
                session.query(Message.id)
                .filter(Message.source_id == source.id, Message.ext_id == raw.ext_id)
                .first()
                is not None
            )
            if already_exists:
                return  # дедупликация по (source_id, ext_id)

            try:
                session.add(
                    Message(
                        source_id=source.id,
                        ext_id=raw.ext_id,
                        author_ext_id=raw.author_ext_id,
                        author_handle=raw.author_handle,
                        url=raw.url,
                        text=raw.text,
                        lang=raw.lang,
                        posted_at=raw.posted_at,
                        trigger_hits=trigger_hits,
                        status=status,
                    )
                )
                session.flush()
            except IntegrityError:
                # Гонка на UniqueConstraint(source_id, ext_id) — сообщение уже
                # записано параллельно, это ожидаемо при дедупе, не ошибка.
                session.rollback()
                return

        logger.info(
            "Telegram {}#{}: status={} (триггеров: {})",
            source.handle,
            raw.ext_id,
            status.value,
            len(result.hits),
        )


def _is_int_like(handle: str) -> bool:
    stripped = handle.lstrip("-")
    return stripped.isdigit()


def _build_message_url(handle: str, message_id: int) -> str | None:
    """Публичная ссылка на сообщение, если у чата есть публичный username.

    Для приватных чатов/групп по числовому id публичной ссылки нет — url=None
    (в карточке лида оператор увидит handle источника, этого достаточно)."""

    if _is_int_like(handle):
        return None
    username = handle.lstrip("@")
    return f"https://t.me/{username}/{message_id}"


async def run_forever() -> None:
    """Точка входа для `scripts/run_monitor.py`."""

    monitor = TelegramMonitor()
    await monitor.start()


if __name__ == "__main__":
    asyncio.run(run_forever())
