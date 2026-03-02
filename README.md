# SpeakPilot (Stage 1)

Stage 1 provides a clean Python project skeleton with a runnable manual-text correction pipeline.

## Requirements
- Python 3.11+

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python speakpilot/main.py
```

## What Stage 1 Includes
- Project structure for future app layers (`core`, `ui`, `analytics`)
- Environment-based configuration loading from `.env`
- Logging initialization
- A minimal interactive CLI loop
- Stubbed correction rules and word-level diff rendering
- In-memory session analytics summary

## What Stage 1 Does Not Include
- Audio capture
- Whisper integration
- OpenAI API calls
- PyQt overlay implementation
