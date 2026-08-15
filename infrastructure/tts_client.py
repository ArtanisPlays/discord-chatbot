import hashlib
import logging
import os
import tempfile

import edge_tts

from domain.ports import TTSProvider
from infrastructure.config import get_tts_voice

logger = logging.getLogger("EdgeTTSClient")


class EdgeTTSClient(TTSProvider):
    """TTS via Microsoft Edge's free online voices (edge-tts), no API key.

    Synthesized audio is cached on disk keyed by the text hash so repeated
    replies do not hit the network again.
    """

    def __init__(self, voice: str | None = None, cache_dir: str | None = None):
        self.voice = voice or get_tts_voice()
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "garapizza_tts")
        os.makedirs(self.cache_dir, exist_ok=True)

    async def synthesize(self, text: str) -> str:
        """Synthesize `text` to an MP3 file and return its path."""
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        path = os.path.join(self.cache_dir, f"{digest}.mp3")
        if os.path.exists(path):
            return path

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(path)
        logger.info("Synthesized %d chars of TTS audio (voice=%s)", len(text), self.voice)
        return path
