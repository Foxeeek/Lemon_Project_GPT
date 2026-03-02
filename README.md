# SpeakPilot (Stage 3)

Stage 3 extends SpeakPilot with async grammar correction after STT.

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
python speakpilot/main.py
```

## Stage 3 Flow
Mic -> STT -> SentenceParser -> CorrectionEngine -> DiffEngine -> Console
