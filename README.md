# SpeakPilot (Stage 2)

Stage 2 extends the Stage 1 skeleton with live microphone speech recognition.

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

## Stage 2 Flow
Microphone -> AudioCapture -> STTEngine (faster-whisper) -> SentenceParser -> console output

## Included in Stage 2
- Non-blocking microphone audio capture (`sounddevice`)
- ~2 second PCM16 chunks at 16 kHz mono
- `faster-whisper` STT wrapper module
- Background STT worker so transcription does not block audio capture
- Graceful shutdown with Ctrl+C

## Not Included Yet
- OpenAI integration
- UI overlay
