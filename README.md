# SpeakPilot (Optimization + Interview Mode)

## Requirements
- Python 3.11+

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configure
Create `.env` from `.env.example` and set:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
INTERVIEW_MODE=false
```

## Run
```bash
python -m speakpilot.main
```
