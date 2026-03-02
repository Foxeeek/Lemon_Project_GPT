"""Sentence parsing utilities."""

from __future__ import annotations

import re


class SentenceParser:
    """Split free-form text into individual sentences."""

    _split_pattern = re.compile(r"[.!?]+")

    def feed_text(self, text: str) -> list[str]:
        """Return non-empty sentence chunks split by basic punctuation."""
        parts = self._split_pattern.split(text)
        return [part.strip() for part in parts if part.strip()]
