"""Stage-3 CLI entrypoint for SpeakPilot with async correction pipeline."""

from __future__ import annotations

import logging
import queue
import signal
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from speakpilot.analytics.session_tracker import SessionTracker
from speakpilot.config import load_config
from speakpilot.core.audio_capture import AudioCapture
from speakpilot.core.correction_engine import CorrectionEngine, CorrectionResult
from speakpilot.core.diff_engine import DiffEngine
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
    logger.info("SpeakPilot stage 3 starting")

    sentence_parser = SentenceParser()
    stt_engine = STTEngine()
    correction_engine = CorrectionEngine()
    diff_engine = DiffEngine()
    session_tracker = SessionTracker()
    session_tracker.start()
    audio_capture = AudioCapture()

    audio_queue: queue.Queue[bytes] = queue.Queue()
    stop_event = threading.Event()
    correction_lock = threading.Lock()
    correction_in_progress = False

    def on_audio_chunk(audio_bytes: bytes) -> None:
        audio_queue.put(audio_bytes)

    with ThreadPoolExecutor(max_workers=1) as correction_executor:

        def on_correction_done(future: Future[CorrectionResult]) -> None:
            nonlocal correction_in_progress
            try:
                result = future.result()
                diff_output = diff_engine.format_console(result.original, result.corrected)
                print("==================================")
                print(f"Original: {result.original}")
                print(f"Corrected: {result.corrected}")
                print(diff_output)
                print(f"Explanation: {result.explanation}")
                print("==================================")
                session_tracker.record(result)
            except Exception as exc:
                logger.exception("Correction task failed: %s", exc)
            finally:
                with correction_lock:
                    correction_in_progress = False

        def stt_worker() -> None:
            nonlocal correction_in_progress
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
                    with correction_lock:
                        if correction_in_progress:
                            logger.info("Skipping sentence while correction is in progress: %s", sentence)
                            continue

                        correction_in_progress = True
                        future = correction_executor.submit(correction_engine.correct, sentence)
                        future.add_done_callback(on_correction_done)

        worker = threading.Thread(target=stt_worker, daemon=True)
        worker.start()

        def request_shutdown(_sig: int, _frame: object) -> None:
            _ = _frame
            logger.info("Shutdown requested")
            stop_event.set()

        signal.signal(signal.SIGINT, request_shutdown)

        print("SpeakPilot Stage 3")
        print("Listening from microphone... Press Ctrl+C to stop.")

        try:
            audio_capture.start(on_audio_chunk)
            while not stop_event.is_set():
                stop_event.wait(0.2)
        finally:
            stop_event.set()
            audio_capture.stop()
            worker.join(timeout=2.0)

    print("Session Summary")
    print(session_tracker.summary())
    logger.info("SpeakPilot stage 3 stopped")


if __name__ == "__main__":
    run()
