# SpeakPilot (Stage 4)

Stage 4 adds a real PyQt6 overlay UI to the async microphone correction pipeline.

## Requirements
- Python 3.11+

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configure
Add your API key to `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
```

## Run
```bash
python -m speakpilot.main
```

## Stage 4 Flow
Mic -> STT (English fixed) -> SentenceParser -> CorrectionEngine (async) -> DiffEngine -> Overlay UI
