"""Reddit-коннектор (PRAW, официальный API, бесплатный тариф) — §4 ТЗ, MVP.

Опрос новых постов/комментариев в сабах из реестра sources (platform="reddit")
каждые 10–30 мин (расписание — в agents/monitor.py через APScheduler).

TODO(этап 1, MVP): реализовать через praw.Reddit(client_id=..., client_secret=...,
user_agent=...) и subreddit.new()/subreddit.comments(). Сетевой код пока не
добавлен — это только каркас интерфейса.
"""

from __future__ import annotations

from connectors.base import RawMessage, SourceConnector


class RedditConnector(SourceConnector):
    """Коннектор Reddit (PRAW)."""

    platform = "reddit"

    def poll(self) -> list[RawMessage]:
        raise NotImplementedError("TODO: реализовать через praw.Reddit(...).subreddit(...).new()")
