import os
import time

from domain.models import ChatMessage, Conversation
from domain.ports import ConversationStore


class MemoryConversationStore(ConversationStore):
    """In-memory per-channel conversation memory (lost on restart)."""

    def __init__(self, max_messages: int | None = None, ttl_seconds: float | None = None):
        self.max_messages = max_messages if max_messages is not None else int(os.getenv("CHAT_HISTORY_MESSAGES", "20"))
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else float(os.getenv("CHAT_HISTORY_TTL", "1800"))
        self._conversations: dict[int, Conversation] = {}

    def get(self, channel_id: int) -> list[ChatMessage]:
        """Prior turns for a channel, or [] if the conversation is stale/empty."""
        conv = self._conversations.get(channel_id)
        if not conv:
            return []
        if time.time() - conv.last_activity > self.ttl_seconds:
            self._conversations.pop(channel_id, None)
            return []
        return list(conv.messages)

    def add(self, channel_id: int, message: ChatMessage) -> None:
        """Remember one turn of a channel's conversation (trimmed to a max size)."""
        conv = self._conversations.setdefault(channel_id, Conversation())
        conv.messages.append(message)
        conv.last_activity = time.time()
        if len(conv.messages) > self.max_messages:
            del conv.messages[: len(conv.messages) - self.max_messages]

    def clear(self, channel_id: int) -> None:
        self._conversations.pop(channel_id, None)
