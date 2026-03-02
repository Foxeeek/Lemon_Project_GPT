"""Microphone audio capture for SpeakPilot stage 2."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd


class AudioCapture:
    """Capture microphone audio in non-blocking chunks and emit bytes callbacks."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_seconds: float = 2.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_seconds = chunk_seconds
        self._target_frames = int(sample_rate * chunk_seconds)

        self._logger = logging.getLogger("speakpilot.audio_capture")
        self._stream: sd.InputStream | None = None
        self._callback: Callable[[bytes], None] | None = None
        self._buffer = np.empty((0,), dtype=np.float32)
        self._lock = threading.Lock()

    def start(self, callback: Callable[[bytes], None]) -> None:
        """Start microphone capture and emit ~2 second PCM16 chunks."""
        if self._stream is not None:
            self._logger.warning("Audio capture already started")
            return

        self._callback = callback
        self._buffer = np.empty((0,), dtype=np.float32)

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._on_audio,
        )
        self._stream.start()
        self._logger.info("Audio capture started")

    def stop(self) -> None:
        """Stop microphone capture."""
        if self._stream is None:
            return

        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._logger.info("Audio capture stopped")

    def _on_audio(self, indata: np.ndarray, frames: int, _time: object, status: sd.CallbackFlags) -> None:
        if status:
            self._logger.warning("Audio callback status: %s", status)

        _ = frames
        if self._callback is None:
            return

        mono = indata[:, 0] if indata.ndim > 1 else indata

        with self._lock:
            self._buffer = np.concatenate((self._buffer, mono.copy()))

            while self._buffer.size >= self._target_frames:
                chunk = self._buffer[: self._target_frames]
                self._buffer = self._buffer[self._target_frames :]

                pcm16 = np.clip(chunk, -1.0, 1.0)
                pcm16 = (pcm16 * 32767.0).astype(np.int16)
                self._callback(pcm16.tobytes())
