"""Speech-to-text engine wrapper for faster-whisper."""

from __future__ import annotations

import logging

import numpy as np
from faster_whisper import WhisperModel


class STTEngine:
    """Transcribe PCM16 mono audio bytes into plain text using faster-whisper."""

    def __init__(self, model_size: str = "base", confidence_threshold: float = -1.0) -> None:
        self._logger = logging.getLogger("speakpilot.stt_engine")
        self._model = WhisperModel(model_size)
        self._confidence_threshold = confidence_threshold

    def transcribe(self, audio_bytes: bytes) -> str:
        """Return plain transcribed text for a PCM16 audio chunk."""
        if not audio_bytes:
            return ""

        try:
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self._model.transcribe(audio, language="en", task="transcribe")
            segment_list = list(segments)
            if not segment_list:
                return ""

            avg_log_prob = sum(segment.avg_logprob for segment in segment_list) / len(segment_list)
            if avg_log_prob < self._confidence_threshold:
                return ""

            text = " ".join(segment.text.strip() for segment in segment_list).strip()
            if not text or not text.strip():
                return ""
            return text
        except Exception as exc:  # graceful runtime handling
            self._logger.exception("STT transcription failed: %s", exc)
            return ""
