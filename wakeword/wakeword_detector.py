import audioop
import time
from typing import Optional


class WakeWordDetector:
    """Very lightweight energy-based wake detector.

    This is **not** a production wake-word model, but it gives the state machine
    a concrete signal to react to. The detector analyses the average energy of
    incoming audio chunks and triggers when it observes a burst that looks like
    a spoken phrase. Cool-down tracking avoids repeated triggers while the user
    keeps talking. Replace this with a proper keyword spotter when available.
    """

    def __init__(
        self,
        wakeword: str = "hey baymax",
        debug_interval: float = 0.0,
        energy_threshold: int = 300,
        required_hits: int = 3,
        cooldown_seconds: float = 2.0,
    ):
        self.wakeword = wakeword.lower()
        self._debug_interval = max(debug_interval, 0.0)
        self._energy_threshold = max(energy_threshold, 1)
        self._required_hits = max(required_hits, 1)
        self._cooldown = max(cooldown_seconds, 0.0)

        self._last_debug_ts = 0.0
        self._last_trigger_ts = 0.0
        self._consecutive_hits = 0

    def _maybe_debug(self, message: str) -> None:
        if self._debug_interval <= 0:
            return

        now = time.monotonic()
        if now - self._last_debug_ts >= self._debug_interval:
            print(message)
            self._last_debug_ts = now

    def detect(self, audio_chunk: Optional[bytes]) -> bool:
        if not audio_chunk:
            self._maybe_debug("[WakeWord] Waiting for audio input …")
            self._consecutive_hits = 0
            return False

        try:
            energy = audioop.rms(audio_chunk, 2)  # assumes 16-bit audio
        except Exception as exc:
            self._maybe_debug(f"[WakeWord] Energy calc error: {exc}")
            return False

        if energy >= self._energy_threshold:
            self._consecutive_hits += 1
            self._maybe_debug(f"[WakeWord] Energy spike detected ({energy})")
        else:
            # decay the counter slowly so short pauses are tolerated
            self._consecutive_hits = max(self._consecutive_hits - 1, 0)

        now = time.monotonic()
        if (
            self._consecutive_hits >= self._required_hits
            and (now - self._last_trigger_ts) >= self._cooldown
        ):
            self._last_trigger_ts = now
            self._consecutive_hits = 0
            self._maybe_debug("[WakeWord] Triggered wake event")
            return True

        return False
