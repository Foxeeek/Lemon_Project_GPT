"""Correction engine interface and stage-1 rule-based stub implementation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Mistake:
    wrong: str
    correct: str
    type: str


@dataclass(slots=True)
class CorrectionResult:
    original: str
    corrected: str
    mistakes: list[Mistake]
    explanation: str


class CorrectionEngine:
    """Apply lightweight demo correction rules for stage 1."""

    def correct(self, sentence: str) -> CorrectionResult:
        original = sentence.strip()
        lowered = original.lower()

        if "i go yesterday" in lowered:
            corrected = self._replace_case_insensitive(original, "I go yesterday", "I went yesterday")
            return CorrectionResult(
                original=original,
                corrected=corrected,
                mistakes=[Mistake(wrong="go", correct="went", type="Tense")],
                explanation="Adjusted verb tense to match past-time marker 'yesterday'.",
            )

        if "in internet" in lowered:
            corrected = self._replace_case_insensitive(original, "in internet", "on the internet")
            return CorrectionResult(
                original=original,
                corrected=corrected,
                mistakes=[Mistake(wrong="in internet", correct="on the internet", type="Prepositions")],
                explanation="Updated preposition phrase to the natural expression.",
            )

        if "i am agree" in lowered:
            corrected = self._replace_case_insensitive(original, "I am agree", "I agree")
            return CorrectionResult(
                original=original,
                corrected=corrected,
                mistakes=[Mistake(wrong="am agree", correct="agree", type="Grammar")],
                explanation="Removed unnecessary auxiliary verb for 'agree'.",
            )

        return CorrectionResult(
            original=original,
            corrected=original,
            mistakes=[],
            explanation="Looks good.",
        )

    @staticmethod
    def _replace_case_insensitive(text: str, source: str, replacement: str) -> str:
        """Replace the first instance of source in text, case-insensitively."""
        index = text.lower().find(source.lower())
        if index == -1:
            return text
        return text[:index] + replacement + text[index + len(source) :]
