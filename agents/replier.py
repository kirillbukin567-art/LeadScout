"""Dialogue Manager — оркестрация обработки входящих ответов лидов (ТЗ §5, §8.3, §9).

M2 (копайлот): входящий ответ → уведомление оператору с черновиком реплики →
[Отправить]/[Редактировать]/[Взять на себя]. M3 (v2, per-dialogue автопилот):
если оператор включил тумблер для конкретного диалога — реплика уходит
автоматически, если LLM не выставил `escalate=true` (§3, §8.3).

TODO(этап 2, v2 для M3): реализовать обработку входящих + логику эскалации.
Сетевой код (сам вызов LLM) — внутри llm/replier.py.
"""

from __future__ import annotations

from core.models import Dialogue
from llm.replier import Replier


class DialogueManagerAgent:
    """Обрабатывает входящее сообщение лида и готовит/отправляет реплику."""

    def __init__(self, replier: Replier | None = None) -> None:
        self.replier = replier or Replier()

    def handle_incoming(self, dialogue: Dialogue, incoming_text: str) -> None:
        """Добавляет реплику лида в transcript_json, генерирует ответ через LLM Replier.

        В режиме copilot — сохраняет черновик и уведомляет оператора.
        В режиме auto (M3) — при escalate=false и включённом тумблере отправляет
        сам, иначе эскалирует на оператора (Dialogue.escalated = True).
        """

        raise NotImplementedError(
            "TODO: обновить transcript_json; self.replier.reply(transcript, lead_card) -> "
            "DialogueReplyResult; ветвление copilot/auto по Dialogue.mode"
        )
