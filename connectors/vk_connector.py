"""VK-коннектор (официальный VK API) — §4 ТЗ, v1.1.

Мониторит посты и комментарии в публичных крипто-группах (реестр sources,
platform="vk"). Опрос каждые 10–30 мин.

TODO(этап 3, v1.1): реализовать через requests к VK API (wall.get / newsfeed.search)
с settings.vk_token. Сетевой код пока не добавлен — это только каркас интерфейса.
"""

from __future__ import annotations

from connectors.base import RawMessage, SourceConnector


class VKConnector(SourceConnector):
    """Коннектор VK API."""

    platform = "vk"

    def poll(self) -> list[RawMessage]:
        raise NotImplementedError("TODO: реализовать через VK API wall.get/newsfeed.search")
