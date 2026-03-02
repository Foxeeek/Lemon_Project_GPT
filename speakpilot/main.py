"""Stage-2 CLI entrypoint for SpeakPilot with microphone STT pipeline."""

from __future__ import annotations

import logging
import queue
import signal
import threading

from speakpilot.config import load_config
from speakpilot.core.audio_capture import AudioCapture
from speakpilot.core.sentence_parser import SentenceParser
from speakpilot.core.stt_engine import STTEngine


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger("speakpilot")
    logger.info("SpeakPilot stage 2 starting")

    sentence_parser = SentenceParser()
    stt_engine = STTEngine()
    audio_capture = AudioCapture()

    audio_queue: queue.Queue[bytes] = queue.Queue()
    stop_event = threading.Event()

    def on_audio_chunk(audio_bytes: bytes) -> None:
        audio_queue.put(audio_bytes)

    def stt_worker() -> None:
        while not stop_event.is_set() or not audio_queue.empty():
            try:
                audio_bytes = audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            text = stt_engine.transcribe(audio_bytes)
            if not text:
                continue

            sentences = sentence_parser.feed_text(text)
            for sentence in sentences:
                print(f"[STT] {sentence}")

    worker = threading.Thread(target=stt_worker, daemon=True)
    worker.start()

    def request_shutdown(_sig: int, _frame: object) -> None:
        _ = _frame
        logger.info("Shutdown requested")
        stop_event.set()

    signal.signal(signal.SIGINT, request_shutdown)

    print("SpeakPilot Stage 2")
    print("Listening from microphone... Press Ctrl+C to stop.")

    try:
        audio_capture.start(on_audio_chunk)
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        stop_event.set()
        audio_capture.stop()
        worker.join(timeout=2.0)
        logger.info("SpeakPilot stage 2 stopped")


if __name__ == "__main__":
    run()
