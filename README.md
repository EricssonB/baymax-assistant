# Baymax Assistant

Voice-first companion modeled after Baymax that idles patiently, wakes on command, holds short conversations, and gracefully returns to sleep. The project showcases production readiness: resilient streaming pipelines, state-machine orchestration, regression tests, and clear developer ergonomics.

---

## Elevator Pitch
- **Use case:** Always-on assistant that listens for “Hey Baymax,” offers empathetic replies via OpenAI, and speaks responses using ElevenLabs.
- **What stands out:** Robust wake/sleep loop, retry-aware streaming STT/TTS, and an idle monitor that prevents prompt spam.
- **Interview hook:** Demonstrates ability to blend real-time audio handling, external APIs, and defensive engineering within a clean architecture.

## Architecture Overview
- **State machine:** `app_states/` drives Wake → Listening → Processing → Speaking → Idle transitions with an injectable `StateManager`.
- **Streaming STT:** `stt/deepgram_stt.py` maintains a live Deepgram websocket, handles reconnection, and debounces post-speech wake triggers via a 3s mute window.
- **LLM layer:** `llm/openai_llm.py` wraps OpenAI for empathetic responses, isolating prompt strategy from transport concerns.
- **TTS pipeline:** `tts/elevenlabs_tts.py` (retries + WAV persistence) produces 16 kHz PCM audio for playback.
- **Idle monitor:** `core/idle_monitor.py` emits a 45s “still there?” nudge and sleeps after 60s of inactivity without colliding with the speaking state.

```
audio mic → Deepgram stream → transcription callbacks
 → OpenAI response → ElevenLabs speech → local WAV
 → idle monitor feedback loop → state transitions
```

## Setup Checklist
1. Install Python 3.11.
2. Create `.env` beside this README:
	```
	DEEPGRAM_API_KEY=your-key
	OPENAI_API_KEY=your-key
	ELEVENLABS_API_KEY=your-key
	```
3. Create and activate the virtual environment:
	```bash
	python3 -m venv venv
	source venv/bin/activate  # macOS/Linux
	```
4. Install pinned dependencies:
	```bash
	pip install -r requirements.txt
	```
5. (macOS) Run once and grant microphone access when prompted in System Settings → Privacy & Security → Microphone.

## Running the Experience
1. Activate the virtual environment (`source venv/bin/activate`).
2. Start the assistant:
	```bash
	python3 main.py
	```
- Baymax announces readiness, listens for “Hey Baymax,” and starts a conversational loop.
- Saying “Goodbye Baymax” triggers the satisfaction check, confirms shutdown desire, and returns to sleep.
- Let the assistant idle to observe warning/sleep prompts at 45s/60s.

## Testing Strategy
- Targeted regression in `tests/test_sleep_flow.py` covers wake → conversation → satisfaction → sleep.
- Run locally:
  ```bash
  python3 -m unittest tests/test_sleep_flow.py
  ```
- Test doubles simulate Deepgram/ElevenLabs/OpenAI, ensuring deterministic behaviour.

## Reliability Highlights
- ElevenLabs client retries with exponential backoff (0.0/0.5/1.5s) before surfacing errors.
- Deepgram websocket reconnects on any dropped connection and replays buffered audio frames.
- Post-speech mute window shields the wake detector from Baymax’s own voice.
- Idle monitor respects the speaking state to avoid overlapping prompts.

## Troubleshooting Guide
- **No microphone audio:** Grant macOS mic access via *System Settings → Privacy & Security → Microphone*.
- **Missing voice output:** Confirm `ELEVENLABS_API_KEY`; inspect `audio/output.wav` for newly written frames.
- **Wake phrase ignored:** Ensure the spoken phrase matches `settings.WAKE_PHRASE` and allow the 3s post-speech mute window before speaking again.
- **Idle prompt spam:** If warnings fire before 45s, check for overlapping playback devices or double-running processes.
- **API rate limits:** Briefly pause and retry; clients already attempt short backoff sequences.

## Opportunities for Iteration
- Expand regression suite with live audio fixtures and negative-path scenarios (e.g., API outages).
- Add CLI flags for alternate personalities or languages.
- Ship a lightweight UI dashboard for live session telemetry (latency, retries, active state).

---

**Owner:** Eric B.  •  **Focus Areas:** Real-time audio processing, API reliability, state-machine design.
