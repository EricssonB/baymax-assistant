import os
import unittest

from app_states.state_manager import StateManager
from core.events import TranscriptEvent, WakeEvent, WakeEventType


class FakeStreamingService:
    def __init__(self):
        self._wake = []
        self._transcript = []
        self._error = []
        self.is_speaking = False
        self.response_notified = False

    def add_wake_listener(self, callback):
        self._wake.append(callback)

    def add_transcript_listener(self, callback):
        self._transcript.append(callback)

    def add_error_listener(self, callback):
        self._error.append(callback)

    def set_speaking(self, is_speaking: bool) -> None:
        self.is_speaking = is_speaking

    def notify_response_sent(self, duration: float = 0.0, *, buffer_override=None) -> None:
        self.response_notified = True

    # Helpers to fire events for tests
    def emit_wake(self, event: WakeEvent) -> None:
        for callback in self._wake:
            callback(event)

    def emit_transcript(self, event: TranscriptEvent) -> None:
        for callback in self._transcript:
            callback(event)


class FakeTTS:
    def __init__(self):
        self.calls = []
        self.output_path = "tests/_fake_output.wav"
        self.last_duration = 0.0

    def speak(self, text: str) -> None:
        self.calls.append(text)

    @property
    def last_text(self):
        return self.calls[-1] if self.calls else None


class FakeLLM:
    def generate(self, text: str) -> str:
        return f"LLM:{text}"


class FakeTranscript(TranscriptEvent):
    def __init__(self, text: str, is_final: bool = True, should_process: bool = True):
        super().__init__(text=text, is_final=is_final, should_process=should_process, raw=None)

class StateFlowTestCase(unittest.TestCase):
    def setUp(self):
        os.environ["BAYMAX_SKIP_AUDIO"] = "1"
        self.streaming = FakeStreamingService()
        self.tts = FakeTTS()
        llm = FakeLLM()

        self.manager = StateManager(
            mic=None,
            stt=None,
            tts=self.tts,
            wake=None,
            llm=llm,
            stt_stream=self.streaming,
        )

        # Start from an awake posture to exercise goodbye/satisfaction paths.
        self.manager.set_state(self.manager.idle_state)

    def _advance_state(self, steps: int = 2) -> None:
        for _ in range(steps):
            self.manager.update()

    def test_goodbye_transitions_to_sleep(self):
        self.streaming.emit_wake(WakeEvent(WakeEventType.SLEEP, "goodbye baymax"))

        # First update should queue SpeakingState, second performs speech & sleeps.
        self._advance_state()

        self.assertIs(self.manager.current_state, self.manager.sleep_state)
        self.assertEqual(
            self.tts.last_text,
            "I cannot deactivate until you say 'you are satisfied with my care'.",
        )

    def test_satisfaction_confirms_and_sleeps(self):
        self.streaming.emit_wake(WakeEvent(WakeEventType.SATISFIED, "you are satisfied with my care"))

        self._advance_state()

        self.assertIs(self.manager.current_state, self.manager.sleep_state)
        self.assertEqual(
            self.tts.last_text,
            "Thank you. I am grateful that you are satisfied with my care. Entering sleep mode.",
        )

    def test_wake_transcript_drives_conversation(self):
        # Start in listening mode to simulate active conversation loop.
        self.manager.set_state(self.manager.listening_state)

        # Wake event should keep us awake but not interfere with transcript handling.
        self.streaming.emit_wake(WakeEvent(WakeEventType.WAKE, "hey baymax"))

        # Provide a final transcript to process.
        self.streaming.emit_transcript(FakeTranscript("How are you?"))

        # Step through listening -> processing -> speaking transitions.
        self._advance_state(steps=3)

        self.assertIs(self.manager.current_state, self.manager.listening_state)
        self.assertTrue(self.tts.calls)
        self.assertEqual(self.tts.last_text, "LLM:How are you?")
        self.assertTrue(self.streaming.response_notified)


if __name__ == "__main__":
    unittest.main()
