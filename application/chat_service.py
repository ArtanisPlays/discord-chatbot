import logging

from domain.models import ChatMessage
from domain.ports import ConversationStore, LLMProvider

logger = logging.getLogger("ChatService")


class ChatService:
    """Use case: one chat turn with per-channel conversation memory."""

    def __init__(self, provider: LLMProvider, store: ConversationStore):
        self.provider = provider
        self.store = store

    async def chat(
        self,
        content: str,
        user_name: str,
        channel_id: int,
        model: str | None = None,
    ) -> str | None:
        """Generate a reply for `content`, remembering the exchange.

        Returns None when the provider is unavailable or fails, so the
        presentation layer decides what message to show.
        """
        if not self.provider.enabled:
            logger.warning("Chat API is not configured; cannot reply.")
            return None

        history = list(self.store.get(channel_id))
        reply = await self.provider.generate_reply(
            content,
            user_name,
            history=history,
            model=model,
        )
        if not reply:
            logger.error("Chat API returned no reply.")
            return None

        self.store.add(channel_id, ChatMessage("user", content))
        self.store.add(channel_id, ChatMessage("assistant", reply))
        return reply

    def clear(self, channel_id: int) -> None:
        """Forget this channel's conversation."""
        self.store.clear(channel_id)
