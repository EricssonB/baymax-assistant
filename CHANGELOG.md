# Changelog

All notable changes to Baymax Assistant are documented here.

---

## [Unreleased]

### Added
- Streaming STT via Deepgram live websocket with automatic reconnection.
- ElevenLabs TTS with retry/backoff (0 / 0.5 / 1.5 s delays).
- Idle monitor issuing a 45 s warning and 60 s sleep transition.
- Satisfaction flow: "Goodbye Baymax" prompts confirmation; "I am satisfied with my care" gracefully sleeps.
- Regression test suite (`tests/test_sleep_flow.py`) covering wake → conversation → satisfaction → sleep.
- Interviewer-focused README with architecture overview, troubleshooting, and iteration ideas.
- Testing checklist (`TESTING_CHECKLIST.md`) for end-to-end validation.
- Inline docstrings across `elevenlabs_tts.py`, `deepgram_stt.py`, `openai_llm.py`, `state_manager.py`.

### Changed
- Extended post-speech mute window to 3 s to prevent self-wake triggers.
- Increased idle thresholds from 30/45 s to 45/60 s to avoid prompt spam.

### Fixed
- Duplicate idle prompts caused by overlapping TTS playback and STT processing.
- Deepgram websocket drops now handled with automatic reconnection and frame replay.
