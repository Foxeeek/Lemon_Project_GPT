"""Stage-5 CLI entrypoint for SpeakPilot optimization + interview mode."""

from __future__ import annotations

import difflib
import html
import logging
import queue
import signal
import threading
import time
from collections import Counter
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
    """Bridge cross-thread updates into Qt main thread."""

    correction_ready = pyqtSignal(str, str, str)
    summary_ready = pyqtSignal(str)


def _build_corrected_html(original: str, corrected: str) -> str:
    original_words = original.split()
    corrected_words = corrected.split()

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


def _normalize_explanation(explanation: str) -> str:
    return " ".join(explanation.lower().split())


def run() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger("speakpilot")
    logger.info("SpeakPilot optimization + interview mode starting")

    app = QApplication([])
    overlay = OverlayWindow(interview_mode=config.interview_mode)
    overlay.move(80, 80)
    overlay.show()

    bridge = OverlayBridge()
    bridge.correction_ready.connect(overlay.show_correction)
    bridge.summary_ready.connect(overlay.show_summary)

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
    pending_lock = threading.Lock()
    metrics_lock = threading.Lock()

    correction_in_progress = False
    pending_sentence: str | None = None
    last_stt_update = 0.0
    silence_seconds = 1.2 if config.interview_mode else 0.7

    metrics: dict[str, int] = {
        "total_sentences": 0,
        "total_corrections": 0,
    }
    explanation_trends: Counter[str] = Counter()

    def try_submit_correction(sentence: str) -> None:
        nonlocal correction_in_progress
        with correction_lock:
            if correction_in_progress:
                logger.info("Skipping sentence while correction is in progress: %s", sentence)
                return

            correction_in_progress = True
            with metrics_lock:
                metrics["total_sentences"] += 1
            future = correction_executor.submit(correction_engine.correct, sentence)
            future.add_done_callback(on_correction_done)

    def on_audio_chunk(audio_bytes: bytes) -> None:
        audio_queue.put(audio_bytes)

    correction_executor = ThreadPoolExecutor(max_workers=1)

    def on_correction_done(future: Future[CorrectionResult]) -> None:
        nonlocal correction_in_progress
        try:
            result = future.result()
            if result.corrected.strip() != result.original.strip():
                with metrics_lock:
                    metrics["total_corrections"] += 1

            explanation_trends[_normalize_explanation(result.explanation)] += 1

            logger.info("Diff: %s", diff_engine.format_console(result.original, result.corrected))
            corrected_html = _build_corrected_html(result.original, result.corrected)
            bridge.correction_ready.emit(result.original, corrected_html, result.explanation)
            session_tracker.record(result)
        except Exception as exc:
            logger.exception("Correction task failed: %s", exc)
        finally:
            with correction_lock:
                correction_in_progress = False

    def stt_worker() -> None:
        nonlocal pending_sentence, last_stt_update
        while not stop_event.is_set() or not audio_queue.empty():
            try:
                audio_bytes = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            text = stt_engine.transcribe(audio_bytes)
            if not text:
                continue

            now = time.monotonic()
            last_stt_update = now

            sentences = sentence_parser.feed_text(text)
            for sentence in sentences:
                words = sentence.split()
                if len(words) < 3:
                    continue

                if text.rstrip().endswith((".", "?", "!")):
                    try_submit_correction(sentence)
                else:
                    with pending_lock:
                        pending_sentence = sentence

    def debounce_worker() -> None:
        nonlocal pending_sentence
        while not stop_event.is_set():
            time.sleep(0.05)
            with pending_lock:
                candidate = pending_sentence

            if not candidate:
                continue

            if (time.monotonic() - last_stt_update) < silence_seconds:
                continue

            with pending_lock:
                if pending_sentence == candidate:
                    pending_sentence = None
            try_submit_correction(candidate)

    stt_thread = threading.Thread(target=stt_worker, daemon=True)
    stt_thread.start()
    debounce_thread = threading.Thread(target=debounce_worker, daemon=True)
    debounce_thread.start()

    def request_shutdown(_sig: int, _frame: object) -> None:
        _ = _frame
        logger.info("Shutdown requested")
        stop_event.set()
        app.quit()

    signal.signal(signal.SIGINT, request_shutdown)

    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    print("SpeakPilot Optimization + Interview Mode")
    print("Listening from microphone... Press Ctrl+C to stop.")

    try:
        audio_capture.start(on_audio_chunk)
        app.exec()
    finally:
        stop_event.set()
        audio_capture.stop()
        stt_thread.join(timeout=2.0)
        debounce_thread.join(timeout=2.0)
        correction_executor.shutdown(wait=False, cancel_futures=False)

        with metrics_lock:
            total_sentences = metrics["total_sentences"]
            total_corrections = metrics["total_corrections"]

        error_rate = (total_corrections / total_sentences) if total_sentences else 0.0
        fluency_score = max(0.0, 100.0 - (error_rate * 100.0))
        most_common_error = "None"
        if explanation_trends:
            most_common_error = explanation_trends.most_common(1)[0][0]

        summary_text = (
            f"Interview Score: {fluency_score:.0f}/100<br/>"
            f"Sentences: {total_sentences} | Corrections: {total_corrections}<br/>"
            f"Most common error: {html.escape(most_common_error)}"
        )
        bridge.summary_ready.emit(summary_text)

        logger.info(
            "Session summary | sentences=%s corrections=%s error_rate=%.2f fluency=%.1f",
            total_sentences,
            total_corrections,
            error_rate,
            fluency_score,
        )
        logger.info("SpeakPilot stopped")


if __name__ == "__main__":
    run()
