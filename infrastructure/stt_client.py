import logging

from domain.ports import STTProvider
from infrastructure.config import get_stt_language, get_stt_model

logger = logging.getLogger("WhisperSTTClient")


class WhisperSTTClient(STTProvider):
    """Local speech-to-text via faster-whisper (CTranslate2), no API key.

    The Whisper model is downloaded once on first use and cached on disk.
    Transcription is CPU-bound and synchronous, so callers should run it
    off the event loop (e.g. `asyncio.to_thread`).
    """

    def __init__(self, model_size: str | None = None,
                 language: str | None = None,
                 device: str = "cpu",
                 compute_type: str = "int8"):
        self.model_size = model_size or get_stt_model()
        self.language = language if language is not None else get_stt_language()
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper model '%s' (device=%s)...", self.model_size, self.device)
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        """Transcribe the audio file and return the text, or "" on failure."""
        try:
            model = self._get_model()
            segments, _info = model.transcribe(
                audio_path,
                language=self.language,
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text
        except Exception as e:
            logger.error("Transcription failed for %s: %s", audio_path, e)
            return ""
