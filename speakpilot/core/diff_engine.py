"""Console-focused diff formatting."""

from __future__ import annotations

import difflib


class DiffEngine:
    """Produce a readable, word-level diff for console output."""

    def format_console(self, original: str, corrected: str) -> str:
        original_words = original.split()
        corrected_words = corrected.split()

        formatted_tokens: list[str] = []
        for token in difflib.ndiff(original_words, corrected_words):
            prefix = token[:2]
            word = token[2:]
            if prefix == "- ":
                formatted_tokens.append(f"[-{word}]")
            elif prefix == "+ ":
                formatted_tokens.append(f"[+{word}]")
            elif prefix == "  ":
                formatted_tokens.append(word)

        return " ".join(formatted_tokens) if formatted_tokens else "(no differences)"
