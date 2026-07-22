"""SQLAlchemy 2.0 модели данных LeadScout (ТЗ §6 «Модель данных» + §12 стадии
воронки + §16 «Discovery-агент: пополнение реестра источников»).

Таблицы: sources, messages, leads, outreach, dialogues, settings,
daily_counters, feedback, dict_history.

Примечание: сами модели — ORM-сущности (persistence), а не pydantic. Pydantic
используется для DTO/контрактов между слоями (например RawMessage в
connectors/base.py и структурированные ответы LLM в llm/) — см. правило
проекта «pydantic-модели для данных».
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""


def _sa_enum(enum_cls: type[enum.Enum]) -> SAEnum:
    """Хранит enum как строку (значение .value), а не нативный тип БД —
    упрощает миграцию SQLite → Postgres и добавление новых значений."""

    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [member.value for member in e],
        length=32,
    )


# --------------------------------------------------------------------------- #
# Управляемые словари статусов/стадий (все значения — как в ТЗ, verbatim)
# --------------------------------------------------------------------------- #


class MessageStatus(str, enum.Enum):
    """Статус входящего сообщения в конвейере Ingest → Trigger Filter → LLM Scorer (§5, §6)."""

    NEW = "new"
    FILTERED_OUT = "filtered_out"
    SCORED = "scored"
    LEAD = "lead"


class LeadType(str, enum.Enum):
    """Тип лида — двойная квалификация «на ходу» (§8.1, §19)."""

    TRADER = "trader"
    PARTNER = "partner"


class GeoStatus(str, enum.Enum):
    """Результат гео-фильтра по config/geo.yaml (§2.6)."""

    OK = "ok"
    BLOCKED_GEO = "blocked_geo"
    UNKNOWN = "unknown"


class LeadState(str, enum.Enum):
    """Стадии воронки лида.

    Базовый набор — §6 ТЗ: new .. dead/skipped.
    Пост-регистрационные стадии — §12 ТЗ (полная воронка до «активно торгует»):
    registered → cashback_set → funded → active. Эти стадии проставляются
    оператором вручную командой /converted <id> <stage> со сверкой с кабинетом
    BingX (§12), автоматической детекции здесь нет.
    """

    NEW = "new"
    SENT_CARD = "sent_card"
    APPROVED = "approved"
    CONTACTED = "contacted"
    REPLIED = "replied"
    IN_DIALOGUE = "in_dialogue"
    CONVERTED = "converted"
    REGISTERED = "registered"
    CASHBACK_SET = "cashback_set"
    FUNDED = "funded"
    ACTIVE = "active"
    DEAD = "dead"
    SKIPPED = "skipped"


class DialogueMode(str, enum.Enum):
    """Режим диалога: копайлот (черновики + Approve) или автопилот (M3, per-dialogue, v2)."""

    COPILOT = "copilot"
    AUTO = "auto"


class SourceStatus(str, enum.Enum):
    """Статус источника в реестре, пополняемом Scout-агентом (§16)."""

    CANDIDATE = "candidate"
    ACTIVE = "active"
    REJECTED = "rejected"
    STALE = "stale"


class DiscoveredBy(str, enum.Enum):
    """Кто добавил источник в реестр (§16)."""

    SEED = "seed"
    SCOUT = "scout"
    MANUAL = "manual"


class DictAction(str, enum.Enum):
    """Тип изменения словаря триггеров для истории версий (§18)."""

    ADD = "add"
    DEL = "del"


# --------------------------------------------------------------------------- #
# Таблицы
# --------------------------------------------------------------------------- #


class Source(Base):
    """Реестр источников мониторинга (§4, §11 seed из sources.yaml; §16 — Discovery)."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("platform", "handle", name="uq_source_platform_handle"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    handle: Mapped[str] = mapped_column(String(255))
    lang: Mapped[str] = mapped_column(String(8))
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # --- Discovery-агент, §16 ---
    source_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovered_by: Mapped[DiscoveredBy] = mapped_column(
        _sa_enum(DiscoveredBy), default=DiscoveredBy.SEED
    )
    status: Mapped[SourceStatus] = mapped_column(
        _sa_enum(SourceStatus), default=SourceStatus.CANDIDATE, index=True
    )
    stats_leads_30d: Mapped[int] = mapped_column(Integer, default=0)
    stats_msgs_30d: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages: Mapped[list["Message"]] = relationship(back_populates="source")


class Message(Base):
    """Унифицированное входящее сообщение (RawMessage после сохранения в БД), §5, §6."""

    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("source_id", "ext_id", name="uq_message_source_ext"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    ext_id: Mapped[str] = mapped_column(String(255))
    author_ext_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trigger_hits: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MessageStatus] = mapped_column(
        _sa_enum(MessageStatus), default=MessageStatus.NEW, index=True
    )

    source: Mapped["Source"] = relationship(back_populates="messages")
    lead: Mapped["Lead | None"] = relationship(back_populates="message", uselist=False)


class Lead(Base):
    """Лид — кандидат, прошедший LLM-скоринг (§6, §8.1, §12)."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), unique=True)
    platform: Mapped[str] = mapped_column(String(32))
    profile_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lead_type: Mapped[LeadType] = mapped_column(_sa_enum(LeadType), index=True)
    score: Mapped[int] = mapped_column(Integer)
    reasons_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    facts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    geo_status: Mapped[GeoStatus] = mapped_column(_sa_enum(GeoStatus), default=GeoStatus.UNKNOWN)
    state: Mapped[LeadState] = mapped_column(_sa_enum(LeadState), default=LeadState.NEW, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    message: Mapped["Message"] = relationship(back_populates="lead")
    outreach: Mapped[list["Outreach"]] = relationship(back_populates="lead")
    dialogues: Mapped[list["Dialogue"]] = relationship(back_populates="lead")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="lead")


class Outreach(Base):
    """Первое (и не более одного follow-up) касание с лидом (§6, §10)."""

    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    draft_text: Mapped[str] = mapped_column(Text)
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True)

    lead: Mapped["Lead"] = relationship(back_populates="outreach")


class Dialogue(Base):
    """Диалог с лидом после ответа: копайлот-черновики реплик или автопилот M3 (§6, §9)."""

    __tablename__ = "dialogues"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    mode: Mapped[DialogueMode] = mapped_column(_sa_enum(DialogueMode), default=DialogueMode.COPILOT)
    last_incoming_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship(back_populates="dialogues")


class SettingRecord(Base):
    """Хранилище настроек «ключ-значение»: режим, пороги, лимиты (§6, §9)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class DailyCounter(Base):
    """Дневные счётчики отправок для rate limiter (§6, §10)."""

    __tablename__ = "daily_counters"

    date: Mapped[str] = mapped_column(String(10), primary_key=True)  # формат YYYY-MM-DD
    platform: Mapped[str] = mapped_column(String(32), primary_key=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)


class Feedback(Base):
    """Обратная связь оператора (кнопка «Не лид» и др.) для донастройки скоринга (§9, §18)."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))  # например: not_a_lead
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead | None"] = relationship(back_populates="feedback")


class DictHistory(Base):
    """Версионирование изменений словарей триггеров с возможностью отката (§18)."""

    __tablename__ = "dict_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[str] = mapped_column(String(8))
    category: Mapped[str] = mapped_column(String(32))
    phrase: Mapped[str] = mapped_column(Text)
    action: Mapped[DictAction] = mapped_column(_sa_enum(DictAction))
    changed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reverted: Mapped[bool] = mapped_column(Boolean, default=False)
