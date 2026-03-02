"""Speech-to-text engine wrapper for faster-whisper."""

from __future__ import annotations

import logging

import numpy as np
from faster_whisper import WhisperModel


class STTEngine:
    """Transcribe PCM16 mono audio bytes into plain text using faster-whisper."""

    def __init__(self, model_size: str = "base") -> None:
        self._logger = logging.getLogger("speakpilot.stt_engine")
        self._model = WhisperModel(model_size)

    def transcribe(self, audio_bytes: bytes) -> str:
        """Return plain transcribed text for a PCM16 audio chunk."""
        if not audio_bytes:
            return ""

        try:
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self._model.transcribe(audio, language=None)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return text
        except Exception as exc:  # graceful runtime handling
            self._logger.exception("STT transcription failed: %s", exc)
            return ""
