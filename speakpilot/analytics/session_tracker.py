"""Session tracking for stage-1 in-memory analytics."""

from __future__ import annotations

from collections import Counter

from speakpilot.core.correction_engine import CorrectionResult


class SessionTracker:
    """Track corrections and provide summary statistics."""

    def __init__(self) -> None:
        self._started = False
        self._results: list[CorrectionResult] = []

    def start(self) -> None:
        self._started = True

    def record(self, result: CorrectionResult) -> None:
        if not self._started:
            self.start()
        self._results.append(result)

    def summary(self) -> dict:
        mistake_categories: Counter[str] = Counter()
        total_corrections = 0

        for result in self._results:
            if result.mistakes:
                total_corrections += 1
                for mistake in result.mistakes:
                    mistake_categories[mistake.type] += 1

        return {
            "total_sentences": len(self._results),
            "total_corrections": total_corrections,
            "mistake_categories": dict(mistake_categories),
        }
