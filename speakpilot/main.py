"""Stage-4 CLI entrypoint for SpeakPilot with async correction + PyQt overlay."""

from __future__ import annotations

import html
import logging
import queue
import signal
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

from speakpilot.analytics.session_tracker import SessionTracker
from speakpilot.config import load_config
from speakpilot.core.audio_capture import AudioCapture
from speakpilot.core.correction_engine import CorrectionEngine, CorrectionResult
from speakpilot.core.diff_engine import DiffEngine
from speakpilot.core.sentence_parser import SentenceParser
from speakpilot.core.stt_engine import STTEngine
from speakpilot.ui.overlay import OverlayWindow


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


class OverlayBridge(QObject):
    """Bridge cross-thread correction updates into Qt main thread."""

    correction_ready = pyqtSignal(str, str, str)


def _build_corrected_html(original: str, corrected: str) -> str:
    original_words = original.split()
    corrected_words = corrected.split()

    import difflib

    chunks: list[str] = []
    matcher = difflib.SequenceMatcher(a=original_words, b=corrected_words)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        words = corrected_words[j1:j2]
        if not words:
            continue
        segment = html.escape(" ".join(words))
        if tag in {"replace", "insert"}:
            chunks.append(
                "<span style='background-color: rgba(72, 187, 120, 0.35); "
                "border-radius: 4px; padding: 1px 3px;'>"
                f"{segment}</span>"
            )
        elif tag == "equal":
            chunks.append(segment)

    return " ".join(chunks) if chunks else html.escape(corrected)


def run() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger("speakpilot")
    logger.info("SpeakPilot stage 4 starting")

    app = QApplication([])
    overlay = OverlayWindow()
    overlay.move(80, 80)
    overlay.show()

    bridge = OverlayBridge()
    bridge.correction_ready.connect(overlay.show_correction)

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

    correction_executor = ThreadPoolExecutor(max_workers=1)

    def on_correction_done(future: Future[CorrectionResult]) -> None:
        nonlocal correction_in_progress
        try:
            result = future.result()
            diff_output = diff_engine.format_console(result.original, result.corrected)
            corrected_html = _build_corrected_html(result.original, result.corrected)

            logger.info("Correction complete | Original: %s | Corrected: %s", result.original, result.corrected)
            logger.info("Diff: %s", diff_output)

            bridge.correction_ready.emit(result.original, corrected_html, result.explanation)
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
        app.quit()

    signal.signal(signal.SIGINT, request_shutdown)

    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    print("SpeakPilot Stage 4")
    print("Listening from microphone... Press Ctrl+C to stop.")

    try:
        audio_capture.start(on_audio_chunk)
        app.exec()
    finally:
        stop_event.set()
        audio_capture.stop()
        worker.join(timeout=2.0)
        correction_executor.shutdown(wait=False, cancel_futures=False)
        logger.info("Session Summary: %s", session_tracker.summary())
        logger.info("SpeakPilot stage 4 stopped")


if __name__ == "__main__":
    run()
