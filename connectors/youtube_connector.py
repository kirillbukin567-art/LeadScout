"""YouTube-коннектор (YouTube Data API v3) — §4 ТЗ, MVP.

Мониторит комментарии под свежими видео целевых крипто-блогеров (список
каналов — в реестре sources, platform="youtube"). Опрос каждые 10–30 мин.

TODO(этап 3): реализовать через googleapiclient.discovery.build("youtube",
"v3", developerKey=settings.youtube_api_key) и commentThreads().list(). Сетевой
код пока не добавлен — это только каркас интерфейса.
"""

from __future__ import annotations

from connectors.base import RawMessage, SourceConnector


class YouTubeConnector(SourceConnector):
    """Коннектор YouTube Data API v3."""

    platform = "youtube"

    def poll(self) -> list[RawMessage]:
        raise NotImplementedError(
            "TODO: реализовать через googleapiclient youtube.commentThreads().list()"
        )
