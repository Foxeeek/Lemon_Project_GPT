"""Stage-1 CLI entrypoint for SpeakPilot."""

from __future__ import annotations

import logging

from speakpilot.analytics.session_tracker import SessionTracker
from speakpilot.config import load_config
from speakpilot.core.correction_engine import CorrectionEngine
from speakpilot.core.diff_engine import DiffEngine
from speakpilot.core.sentence_parser import SentenceParser


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger("speakpilot")
    logger.info("SpeakPilot stage 1 starting")

    sentence_parser = SentenceParser()
    correction_engine = CorrectionEngine()
    diff_engine = DiffEngine()
    session_tracker = SessionTracker()
    session_tracker.start()

    print("SpeakPilot Stage 1")
    print("Type a sentence and press Enter. Type 'exit' to quit.")

    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() == "exit":
            break

        sentences = sentence_parser.feed_text(user_input)
        if not sentences:
            print("No valid sentence detected.")
            continue

        for sentence in sentences:
            result = correction_engine.correct(sentence)
            diff_output = diff_engine.format_console(result.original, result.corrected)
            session_tracker.record(result)

            print("-" * 40)
            print(f"Original   : {result.original}")
            print(f"Corrected  : {result.corrected}")
            print(f"Diff       : {diff_output}")
            print(f"Explanation: {result.explanation}")

    print("\nSession Summary")
    print(session_tracker.summary())


if __name__ == "__main__":
    run()
