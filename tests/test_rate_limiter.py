"""Тесты анти-бан rate limiter'а (ТЗ §10) — лимиты неотключаемы."""

from datetime import datetime

import pytest

from core.rate_limiter import (
    LimitsConfig,
    RateLimiter,
    ReactivationLimits,
    TelegramMonitorLimits,
    TelegramSenderLimits,
    enforce_hard_ceilings,
)


def _valid_config(**overrides) -> LimitsConfig:
    sender_kwargs = {
        "max_cold_messages_per_day": 15,
        "warmup_days": 14,
        "warmup_max_cold_messages_per_day": 5,
        "delay_between_sends_sec_min": 180,
        "delay_between_sends_sec_max": 600,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "08:00",
        "max_follow_ups_per_lead": 1,
        "follow_up_min_days_after_first_contact": 5,
    }
    sender_kwargs.update(overrides)
    return LimitsConfig(
        telegram_sender=TelegramSenderLimits(**sender_kwargs),
        telegram_monitor=TelegramMonitorLimits(max_new_chat_joins_per_day=2),
        reactivation=ReactivationLimits(
            inactive_after_registered_days=14, max_reactivation_contacts_per_lead=1
        ),
        auto_pause_on_flood_wait=True,
        alert_operator_on_auto_pause=True,
    )


def test_valid_config_passes_ceiling_check() -> None:
    enforce_hard_ceilings(_valid_config())  # не должно поднимать исключение


def test_loosening_daily_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_cold_messages_per_day"):
        enforce_hard_ceilings(_valid_config(max_cold_messages_per_day=100))


def test_shortening_warmup_period_is_rejected() -> None:
    with pytest.raises(ValueError, match="warmup_days"):
        enforce_hard_ceilings(_valid_config(warmup_days=1))


def test_daily_cold_limit_respects_warmup() -> None:
    limiter = RateLimiter(_valid_config())
    assert limiter.daily_cold_limit(sender_account_age_days=3) == 5
    assert limiter.daily_cold_limit(sender_account_age_days=30) == 15


def test_can_send_more_today() -> None:
    limiter = RateLimiter(_valid_config())
    assert limiter.can_send_more_today(sent_today=4, sender_account_age_days=3)
    assert not limiter.can_send_more_today(sent_today=5, sender_account_age_days=3)


def test_quiet_hours_overnight_range() -> None:
    limiter = RateLimiter(_valid_config())
    assert limiter.is_quiet_hours(datetime(2026, 1, 1, 23, 30))
    assert limiter.is_quiet_hours(datetime(2026, 1, 1, 3, 0))
    assert not limiter.is_quiet_hours(datetime(2026, 1, 1, 12, 0))


def test_follow_up_requires_min_days_and_max_count() -> None:
    limiter = RateLimiter(_valid_config())
    first_contact = datetime(2026, 1, 1)
    assert not limiter.can_send_follow_up(first_contact, datetime(2026, 1, 3), follow_ups_already_sent=0)
    assert limiter.can_send_follow_up(first_contact, datetime(2026, 1, 7), follow_ups_already_sent=0)
    assert not limiter.can_send_follow_up(first_contact, datetime(2026, 1, 10), follow_ups_already_sent=1)


def test_real_limits_yaml_is_valid() -> None:
    """Реальный config/limits.yaml не должен ослаблять лимиты §10."""

    config = LimitsConfig.from_yaml()
    assert config.telegram_sender.max_cold_messages_per_day <= 15
