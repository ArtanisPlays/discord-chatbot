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


@runtime_checkable
class TTSProvider(Protocol):
    """Contract for text-to-speech synthesis."""

    voice: str

    async def synthesize(self, text: str) -> str:
        """Synthesize `text` into an audio file and return its path."""
        ...


@runtime_checkable
class STTProvider(Protocol):
    """Contract for speech-to-text transcription of an audio file."""

    def transcribe(self, audio_path: str) -> str:
        """Transcribe the audio at `audio_path` and return the text."""
        ...
