import time

from core.events import WakeEventType
from interfaces.state_interface import State


class SleepState(State):
    """Baymax is idle and waiting for the wake word."""

    def __init__(self, poll_interval: float = 0.2):
        self._poll_interval = poll_interval

    def on_enter(self):
        print("[State] >>> SleepState")

    def on_exit(self):
        print("[State] <<< SleepState")

    def handle(self, manager, user_input):
        if hasattr(manager, "sleep_guard_active") and manager.sleep_guard_active():
            if hasattr(manager, "clear_wake_events"):
                manager.clear_wake_events()
            time.sleep(self._poll_interval)
            return None

        # Streaming wake events take precedence when available
        wake_event = manager.peek_wake_event() if manager.streaming_enabled else None
        if wake_event and wake_event.event_type == WakeEventType.WAKE:
            manager.consume_wake_event()
            if hasattr(manager, "clear_transcripts"):
                manager.clear_transcripts()
            if hasattr(manager, "clear_wake_events"):
                manager.clear_wake_events()
            print("[SleepState] Wake word detected (stream)")
            return manager.wake_state

        # Explicit wake directive (useful for tests or CLI shortcuts)
        if isinstance(user_input, str) and user_input.lower() == "hey baymax":
            print("[SleepState] Wake word detected (manual input)!")
            manager.mark_user_activity()
            return manager.wake_state

        if manager.streaming_enabled:
            time.sleep(self._poll_interval)
            return None

        mic = getattr(manager, "mic", None)
        wake = getattr(manager, "wake", None)

        if mic and wake:
            if hasattr(mic, "start_stream"):
                mic.start_stream()
            try:
                audio_chunk = mic.read_audio_chunk()
            except Exception as exc:
                print("[SleepState] Mic read error:", exc)
                time.sleep(self._poll_interval)
                return None

            if audio_chunk:
                try:
                    if wake.detect(audio_chunk):
                        if hasattr(manager, "clear_transcripts"):
                            manager.clear_transcripts()
                        if hasattr(manager, "clear_wake_events"):
                            manager.clear_wake_events()
                        print("[SleepState] Wake word detected!")
                        return manager.wake_state
                except Exception as exc:
                    print("[SleepState] Wake detector error:", exc)
            else:
                # No audio available yet; fall through to sleep
                time.sleep(self._poll_interval)
                return None

        # Either no hardware configured or wake word not found – pause briefly
        time.sleep(self._poll_interval)
        return None
