"""Configuration loading for SpeakPilot."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    openai_api_key: str | None
    log_level: str
    interview_mode: bool


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    load_dotenv()
    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        interview_mode=_to_bool(os.getenv("INTERVIEW_MODE"), default=False),
    )
