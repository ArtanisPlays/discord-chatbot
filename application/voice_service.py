import asyncio
import logging

from domain.ports import STTProvider, TTSProvider
from application.chat_service import ChatService

logger = logging.getLogger("VoiceService")


class VoiceService:
    """Use case: a spoken question answered with text and speech.

    Kept Discord-free: it turns a WAV file into a chat reply and a TTS audio
    file. The presentation layer decides how the audio is played.
    """

    def __init__(self, chat: ChatService, stt: STTProvider, tts: TTSProvider):
        self.chat = chat
        self.stt = stt
        self.tts = tts

    async def transcribe(self, audio_path: str) -> str:
        """Transcribe one audio file (CPU-bound, run off the event loop)."""
        return await asyncio.to_thread(self.stt.transcribe, audio_path)

    async def handle_transcript(self, transcript: str, user_name: str,
                                guild_id: int | None, channel_id: int,
                                model: str | None = None) -> str | None:
        """Send a transcript through the chat pipeline and return the reply."""
        return await self.chat.chat(transcript, user_name, channel_id, model=model)

    async def speak(self, text: str) -> str | None:
        """Synthesize speech for `text`, returning the audio file path."""
        try:
            return await self.tts.synthesize(text)
        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            return None
