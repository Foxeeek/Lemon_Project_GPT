"""Correction engine using OpenAI with compact JSON responses."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


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
    """Correct sentence grammar using OpenAI and return structured results."""

    _SYSTEM_PROMPT = (
        "You are an English grammar corrector.\n"
        "Fix grammar only.\n"
        "Do not change meaning.\n"
        "Return JSON:\n"
        "{\n"
        '  "corrected": string,\n'
        '  "explanation": string (max 15 words)\n'
        "}"
    )

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        self._client = OpenAI(api_key=api_key)

    def correct(self, sentence: str) -> CorrectionResult:
        original = sentence.strip()
        if not original:
            return self._fallback_result(original)

        for _ in range(2):
            try:
                response = self._client.responses.create(
                    model="gpt-4.1-mini",
                    temperature=0.0,
                    input=[
                        {"role": "system", "content": self._SYSTEM_PROMPT},
                        {"role": "user", "content": original},
                    ],
                )
                payload = json.loads(response.output_text)
                return self._parse_result(payload, original)
            except Exception:
                continue

        return self._fallback_result(original)

    def _parse_result(self, payload: Any, original: str) -> CorrectionResult:
        if not isinstance(payload, dict):
            raise ValueError("Response payload is not a JSON object")

        corrected = payload.get("corrected")
        explanation = payload.get("explanation")
        if not isinstance(corrected, str) or not isinstance(explanation, str):
            raise ValueError("Invalid payload fields")

        return CorrectionResult(
            original=original,
            corrected=corrected.strip() or original,
            mistakes=[],
            explanation=explanation.strip() or "Grammar adjusted.",
        )

    @staticmethod
    def _fallback_result(original: str) -> CorrectionResult:
        return CorrectionResult(
            original=original,
            corrected=original,
            mistakes=[],
            explanation="Unable to correct right now.",
        )
