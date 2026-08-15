from typing import Protocol, runtime_checkable

from domain.models import ChatMessage


@runtime_checkable
class LLMProvider(Protocol):
    """Contract for anything that can generate chat replies and list models."""

    model: str
    enabled: bool

    async def generate_reply(
        self,
        user_message: str,
        user_name: str,
        history: list[ChatMessage] | None = None,
        model: str | None = None,
    ) -> str | None: ...

    async def fetch_models(self) -> list[dict]: ...


@runtime_checkable
class ConversationStore(Protocol):
    """Contract for persisting per-channel conversation memory."""

    def get(self, channel_id: int) -> list[ChatMessage]: ...

    def add(self, channel_id: int, message: ChatMessage) -> None: ...

    def clear(self, channel_id: int) -> None: ...
