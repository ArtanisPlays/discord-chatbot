import logging
import os
import shutil
import tempfile
import time

import discord.sinks

logger = logging.getLogger("VoiceReceiver")


class VoiceReceiver:
    """Wraps py-cord's voice recording so each speaker's audio lands on disk.

    Usage:
        receiver = VoiceReceiver()
        receiver.start(vc, on_done)          # start listening
        vc.stop_recording()                  # stop, triggers on_done

    `on_done` is an async callback receiving `(paths: dict[int, str], *args)`
    where paths maps user ids to WAV files saved under `output_dir`.
    """

    def __init__(self, output_dir: str | None = None):
        self.output_dir = output_dir or os.path.join(tempfile.gettempdir(), "garapizza_voice")
        os.makedirs(self.output_dir, exist_ok=True)
        self._on_done = None

    def start(self, vc, on_done, *args) -> bool:
        """Begin recording the connected voice client.

        Returns True if recording started, False if it was already recording.
        """
        if getattr(vc, "is_recording", lambda: False)():
            logger.warning("Already recording; ignoring start request.")
            return False
        self._on_done = on_done
        vc.start_recording(discord.sinks.WaveSink(), self._handle_done, *args)
        logger.info("Started voice recording.")
        return True

    async def _handle_done(self, sink: discord.sinks.Sink, *args) -> None:
        """Flush the sink's audio to WAV files, then call the user callback."""
        paths: dict[int, str] = {}
        for user_id, audio in sink.audio_data.items():
            file = getattr(audio, "file", None)
            if file is None:
                continue
            try:
                file.seek(0)
                path = os.path.join(self.output_dir, f"{user_id}_{int(time.time())}.wav")
                with open(path, "wb") as out:
                    shutil.copyfileobj(file, out)
                paths[user_id] = path
            except Exception as e:
                logger.error("Failed to save audio for user %s: %s", user_id, e)
        try:
            await sink.cleanup()
        except Exception as e:
            logger.warning("Sink cleanup failed: %s", e)
        logger.info("Recording finished: %d speaker(s).", len(paths))
        if self._on_done:
            await self._on_done(paths, *args)
