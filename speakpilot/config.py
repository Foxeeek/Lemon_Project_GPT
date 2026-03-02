"""Configuration loading for SpeakPilot."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    openai_api_key: str | None
    log_level: str


def load_config() -> AppConfig:
    load_dotenv()
    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
