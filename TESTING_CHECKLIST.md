# Testing Checklist

Quick reference for end-to-end validation before release.

---

## Pre-flight

- [ ] `.env` exists with `DEEPGRAM_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`.
- [ ] Dependencies installed (`pip install -r requirements.txt`).
- [ ] macOS mic access granted if prompted previously.

## Automated Regression

```bash
python3 -m unittest tests/test_sleep_flow.py
```

- [ ] All tests pass with no warnings.

## Manual Voice Session

1. **Start assistant**
   ```bash
   python3 main.py
   ```
2. **Wake phrase** – Say "Hey Baymax"; confirm greeting and transition to listening.
3. **Conversation** – Ask a question; verify LLM response plays via TTS.
4. **Goodbye flow** – Say "Goodbye Baymax"; expect satisfaction prompt.
5. **Satisfaction** – Respond "I am satisfied with my care"; confirm graceful sleep.
6. **Idle behavior** – Remain silent ~45 s; confirm single warning, then ~60 s for sleep message without spam.

## Log Audit

- [ ] `[STT]` logs show transcript without excessive retries.
- [ ] `[TTS]` logs confirm WAV written; no "Exhausted retries" errors.
- [ ] `[STATE]` transitions appear in expected order.

## Post-Test

- [ ] Record any anomalies or edge cases for backlog.
- [ ] Commit/tag release if all checks pass.
