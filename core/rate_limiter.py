"""Анти-бан rate limiter (ТЗ §10) — неотключаемые лимиты отправки.

Жёсткое правило проекта: лимиты §10 реализуются в коде и не имеют флага
отключения. Здесь это выражено буквально — жёстко зашитые «потолки»
(_CEILINGS ниже, взяты прямо из §10 ТЗ) проверяются при загрузке
config/limits.yaml: конфиг разрешено только УЖЕСТОЧАТЬ, отключить или
ослабить лимит через конфиг нельзя (при попытке — ValueError при старте).

Модуль не делает сетевых вызовов — только чистая логика проверки лимитов.
Реальные счётчики (сколько уже отправлено сегодня) хранятся в таблице
daily_counters (core/models.py) и передаются сюда как параметры.
"""

from __future__ import annotations

import random
from datetime import datetime, time
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_LIMITS_PATH = CONFIG_DIR / "limits.yaml"

# «Потолки»/«полы» из §10 ТЗ — константы, а не настройки. Направление проверки
# зависит от смысла лимита: для одних параметров конфиг не может ПРЕВЫШАТЬ
# значение (ceiling), для других — не может быть МЕНЬШЕ (floor, например пауза
# между отправками или срок прогрева можно только увеличить).
_CEILING_MAX_COLD_PER_DAY = 15
_CEILING_WARMUP_MAX_PER_DAY = 5
_FLOOR_WARMUP_DAYS = 14
_FLOOR_DELAY_MIN_SEC = 180
_FLOOR_DELAY_MAX_SEC = 600
_CEILING_MAX_FOLLOW_UPS = 1
_FLOOR_FOLLOW_UP_MIN_DAYS = 5
_CEILING_NEW_CHAT_JOINS_PER_DAY = 2


class TelegramSenderLimits(BaseModel):
    max_cold_messages_per_day: int
    warmup_days: int
    warmup_max_cold_messages_per_day: int
    delay_between_sends_sec_min: int
    delay_between_sends_sec_max: int
    quiet_hours_start: str
    quiet_hours_end: str
    max_follow_ups_per_lead: int
    follow_up_min_days_after_first_contact: int


class TelegramMonitorLimits(BaseModel):
    max_new_chat_joins_per_day: int


class ReactivationLimits(BaseModel):
    inactive_after_registered_days: int
    max_reactivation_contacts_per_lead: int


class LimitsConfig(BaseModel):
    """Типизированное представление config/limits.yaml."""

    telegram_sender: TelegramSenderLimits
    telegram_monitor: TelegramMonitorLimits
    reactivation: ReactivationLimits
    auto_pause_on_flood_wait: bool
    alert_operator_on_auto_pause: bool

    @classmethod
    def from_yaml(cls, path: Path | str = DEFAULT_LIMITS_PATH) -> "LimitsConfig":
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        config = cls(**data)
        enforce_hard_ceilings(config)
        return config


def enforce_hard_ceilings(config: LimitsConfig) -> None:
    """Проверяет, что config/limits.yaml не ослабляет лимиты §10 ТЗ.

    Поднимает ValueError при старте приложения, если кто-то попытался
    увеличить лимит отправки через конфиг — это не флаг, это единственная
    защита, поэтому она должна валиться громко и сразу.
    """

    s = config.telegram_sender
    violations: list[str] = []

    if s.max_cold_messages_per_day > _CEILING_MAX_COLD_PER_DAY:
        violations.append(
            f"max_cold_messages_per_day={s.max_cold_messages_per_day} > {_CEILING_MAX_COLD_PER_DAY}"
        )
    if s.warmup_max_cold_messages_per_day > _CEILING_WARMUP_MAX_PER_DAY:
        violations.append(
            "warmup_max_cold_messages_per_day="
            f"{s.warmup_max_cold_messages_per_day} > {_CEILING_WARMUP_MAX_PER_DAY}"
        )
    if s.warmup_days < _FLOOR_WARMUP_DAYS:
        violations.append(f"warmup_days={s.warmup_days} < {_FLOOR_WARMUP_DAYS}")
    if s.delay_between_sends_sec_min < _FLOOR_DELAY_MIN_SEC:
        violations.append(
            f"delay_between_sends_sec_min={s.delay_between_sends_sec_min} < {_FLOOR_DELAY_MIN_SEC}"
        )
    if s.delay_between_sends_sec_max < _FLOOR_DELAY_MAX_SEC:
        violations.append(
            f"delay_between_sends_sec_max={s.delay_between_sends_sec_max} < {_FLOOR_DELAY_MAX_SEC}"
        )
    if s.max_follow_ups_per_lead > _CEILING_MAX_FOLLOW_UPS:
        violations.append(
            f"max_follow_ups_per_lead={s.max_follow_ups_per_lead} > {_CEILING_MAX_FOLLOW_UPS}"
        )
    if s.follow_up_min_days_after_first_contact < _FLOOR_FOLLOW_UP_MIN_DAYS:
        violations.append(
            "follow_up_min_days_after_first_contact="
            f"{s.follow_up_min_days_after_first_contact} < {_FLOOR_FOLLOW_UP_MIN_DAYS}"
        )
    if config.telegram_monitor.max_new_chat_joins_per_day > _CEILING_NEW_CHAT_JOINS_PER_DAY:
        violations.append(
            "telegram_monitor.max_new_chat_joins_per_day="
            f"{config.telegram_monitor.max_new_chat_joins_per_day} > "
            f"{_CEILING_NEW_CHAT_JOINS_PER_DAY}"
        )

    if violations:
        raise ValueError(
            "config/limits.yaml ослабляет неотключаемые лимиты §10 ТЗ: " + "; ".join(violations)
        )


def _parse_hhmm(value: str) -> time:
    hours, minutes = (int(part) for part in value.split(":"))
    return time(hour=hours, minute=minutes)


class RateLimiter:
    """Чистая логика проверки анти-бан лимитов (без сети и без БД)."""

    def __init__(self, limits: LimitsConfig | None = None) -> None:
        self.limits = limits or LimitsConfig.from_yaml()

    def daily_cold_limit(self, sender_account_age_days: int) -> int:
        """Лимит холодных сообщений в день с учётом «прогрева» нового аккаунта."""

        s = self.limits.telegram_sender
        if sender_account_age_days < s.warmup_days:
            return s.warmup_max_cold_messages_per_day
        return s.max_cold_messages_per_day

    def can_send_more_today(self, sent_today: int, sender_account_age_days: int) -> bool:
        return sent_today < self.daily_cold_limit(sender_account_age_days)

    def is_quiet_hours(self, local_now: datetime) -> bool:
        """Ночная тишина по часовому поясу лида (§10). Диапазон может
        переходить через полночь (например 23:00–08:00)."""

        s = self.limits.telegram_sender
        start = _parse_hhmm(s.quiet_hours_start)
        end = _parse_hhmm(s.quiet_hours_end)
        now = local_now.time()
        if start <= end:
            return start <= now < end
        return now >= start or now < end

    def random_delay_seconds(self) -> int:
        """Случайная пауза между отправками (§10)."""

        s = self.limits.telegram_sender
        return random.randint(s.delay_between_sends_sec_min, s.delay_between_sends_sec_max)

    def can_send_follow_up(
        self, first_contact_at: datetime, now: datetime, follow_ups_already_sent: int
    ) -> bool:
        """Follow-up не более 1, не раньше N дней после первого касания (§10)."""

        s = self.limits.telegram_sender
        if follow_ups_already_sent >= s.max_follow_ups_per_lead:
            return False
        return (now - first_contact_at).days >= s.follow_up_min_days_after_first_contact

    def can_join_new_chat(self, joins_today: int) -> bool:
        return joins_today < self.limits.telegram_monitor.max_new_chat_joins_per_day
