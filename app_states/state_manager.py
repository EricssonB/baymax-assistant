# app_states/state_manager.py

import threading
import time
from collections import deque
from typing import Deque, Optional

from config_app.settings import settings

from interfaces.state_interface import State
from app_states.sleep_state import SleepState
from app_states.wake_state import WakeState
from app_states.listening_state import ListeningState
from app_states.processing_state import ProcessingState
from app_states.speaking_state import SpeakingState
from app_states.idle_state import IdleState
from core.events import TranscriptEvent, WakeEvent, WakeEventType

class StateManager:
    """
    Central orchestrator for Baymax's state machine.

    Responsibilities:
    - Owns instances of all states (Sleep, Wake, Listening, Processing, Speaking, Idle).
    - Injects external modules (mic, stt, tts, llm, streaming_stt) into relevant states.
    - Guarantees on_exit/on_enter hooks fire on every transition.
    - Routes wake/transcript events from the streaming STT to appropriate handlers.
    - Tracks idle timers and user activity timestamps.
    """

    def __init__(self, mic=None, stt=None, tts=None, wake=None, llm=None, stt_stream=None):
        # External modules
        self.mic = mic
        self.stt = stt
        self.tts = tts
        self.wake = wake
        self.llm = llm   # <-- Required fix
        self.streaming_stt = stt_stream

        # Shared conversation variables
        self.last_user_text = None
        self.last_bot_text = None

        now = time.time()
        self._last_user_activity_ts = now
        self._last_awake_ts = 0.0
        self._idle_warning_message = "I'm here if you need me."
        self._idle_sleep_message = "Let me know if you need me."

        self._post_speech_state: Optional[State] = None
        self._pending_sleep_message = "I cannot deactivate until you say 'you are satisfied with my care'."
        self._satisfaction_confirmation = "Thank you. I am grateful that you are satisfied with my care. Entering sleep mode."

        self._event_lock = threading.Lock()
        self._wake_events: Deque[WakeEvent] = deque()
        self._transcript_events: Deque[TranscriptEvent] = deque()
        self._speech_cooldown_until = 0.0
        self._sleep_guard_until = 0.0
        self._sleep_guard_pending = 0.0

        if self.streaming_stt:
            self.streaming_stt.add_wake_listener(self._on_wake_event)
            self.streaming_stt.add_transcript_listener(self._on_transcript_event)
            self.streaming_stt.add_error_listener(self._on_stream_error)

        # Instantiate states (inject dependencies here)
        self.sleep_state = SleepState()
        self.wake_state = WakeState()
        self.listening_state = ListeningState(mic=self.mic, stt=self.stt)
        self.processing_state = ProcessingState(llm=self.llm)
        self.speaking_state = SpeakingState(tts=self.tts)
        self.idle_state = IdleState()

        # Initial state
        self.current_state: State = self.sleep_state

        # Run on_enter hook for initial state
        enter_hook = getattr(self.current_state, "on_enter", None)
        if enter_hook:
            enter_hook()

    def set_state(self, new_state: State) -> None:
        """Transition to `new_state`, invoking exit/enter hooks as needed."""
        if not new_state or new_state is self.current_state:
            return

        # Exit previous state
        exit_hook = getattr(self.current_state, "on_exit", None)
        if exit_hook:
            exit_hook()

        # Visual separation between state logs for readability
        print()

        # Switch state
        previous_state = self.current_state
        self.current_state = new_state

        # Enter new state
        enter_hook = getattr(self.current_state, "on_enter", None)
        if enter_hook:
            enter_hook()

        if new_state is self.sleep_state:
            if self._sleep_guard_pending > 0.0:
                self._sleep_guard_until = time.time() + self._sleep_guard_pending
                self._sleep_guard_pending = 0.0
            self._mark_sleep()
        elif previous_state is self.sleep_state:
            self._mark_awake()

    def update(self, user_input=None):
        """Run one tick of the state machine, processing events and delegating to the current state."""
        if self.streaming_enabled and self._process_wake_directives():
            return

        next_state = self.current_state.handle(self, user_input)

        if next_state and next_state != self.current_state:
            self.set_state(next_state)

        if self.streaming_enabled:
            self._process_wake_directives()

    # ------------------------------------------------------------------
    # Event helpers used by states
    # ------------------------------------------------------------------
    def consume_wake_event(self) -> Optional[WakeEvent]:
        event = self._pop_wake_event()
        return event

    def consume_transcript(self) -> Optional[str]:
        with self._event_lock:
            if not self._transcript_events:
                return None
            event = self._transcript_events.popleft()
        self.last_user_text = event.text
        self.mark_user_activity()
        return event.text

    @property
    def streaming_enabled(self) -> bool:
        return self.streaming_stt is not None

    @property
    def is_awake(self) -> bool:
        return self.current_state is not self.sleep_state

    @property
    def is_speaking(self) -> bool:
        return self.current_state is self.speaking_state

    @property
    def last_user_activity(self) -> float:
        return self._last_user_activity_ts

    def peek_wake_event(self) -> Optional[WakeEvent]:
        with self._event_lock:
            return self._wake_events[0] if self._wake_events else None

    def notify_speaking_start(self) -> None:
        if self.streaming_stt:
            self.streaming_stt.set_speaking(True)

    def notify_speaking_end(self, duration: float = 0.0) -> None:
        post_sleep_transition = self._post_speech_state is self.sleep_state

        buffer = max(settings.TTS_POST_BUFFER, 0.0)
        if post_sleep_transition:
            buffer = max(buffer, settings.SLEEP_ENTRY_GUARD)

        if self.streaming_stt:
            self.streaming_stt.set_speaking(False)
            self.streaming_stt.notify_response_sent(duration, buffer_override=buffer)

        self._speech_cooldown_until = max(self._speech_cooldown_until, time.time() + buffer)

        mic = getattr(self, "mic", None)
        if mic and hasattr(mic, "mute_for"):
            try:
                mic.mute_for(buffer)
            except Exception:
                pass

    def set_post_speech_state(self, state: Optional[State]) -> None:
        self._post_speech_state = state

    def consume_post_speech_state(self) -> Optional[State]:
        state = self._post_speech_state
        self._post_speech_state = None
        return state

    def mark_user_activity(self) -> None:
        self._last_user_activity_ts = time.time()

    def clear_transcripts(self) -> None:
        self._clear_transcripts()

    def sleep_guard_active(self) -> bool:
        return time.time() < self._sleep_guard_until

    def arm_sleep_guard(self, duration: float) -> None:
        self._sleep_guard_pending = max(self._sleep_guard_pending, max(duration, 0.0))

    def clear_wake_events(self) -> None:
        with self._event_lock:
            self._wake_events.clear()

    def speaking_cooldown_active(self) -> bool:
        return self.speaking_cooldown_remaining() > 0.0

    def speaking_cooldown_remaining(self) -> float:
        return max(self._speech_cooldown_until - time.time(), 0.0)

    def queue_idle_prompt(self) -> None:
        if not self.is_awake:
            return
        if self.is_speaking:
            return
        if self.last_bot_text:
            return

        self.last_bot_text = self._idle_warning_message
        self.set_post_speech_state(self.idle_state)
        self.set_state(self.speaking_state)

    def queue_idle_sleep_message(self) -> None:
        if self.current_state is self.sleep_state:
            return
        if self.is_speaking:
            return

        self.last_user_text = None
        self.last_bot_text = self._idle_sleep_message
        self.set_post_speech_state(self.sleep_state)
        self._clear_transcripts()
        self.arm_sleep_guard(settings.SLEEP_ENTRY_GUARD)
        self.clear_wake_events()
        self.set_state(self.speaking_state)

    # ------------------------------------------------------------------
    # Streaming event listeners
    # ------------------------------------------------------------------
    def _on_wake_event(self, event: WakeEvent) -> None:
        with self._event_lock:
            self._wake_events.append(event)
        if event.event_type == WakeEventType.WAKE:
            self.mark_user_activity()

    def _on_transcript_event(self, event: TranscriptEvent) -> None:
        if not event.is_final or not event.should_process:
            return
        with self._event_lock:
            self._transcript_events.append(event)
        self.mark_user_activity()

    def _on_stream_error(self, exc: Exception) -> None:
        print("[STT] Streaming error:", exc)

    def _pop_wake_event(self) -> Optional[WakeEvent]:
        with self._event_lock:
            if self._wake_events:
                return self._wake_events.popleft()
        return None

    def _process_wake_directives(self) -> bool:
        transitioned = False

        while True:
            event = self.peek_wake_event()
            if not event or event.event_type == WakeEventType.WAKE:
                break

            # Consume the event and transition to SleepState
            self._pop_wake_event()
            if event.event_type == WakeEventType.SLEEP:
                if self.current_state is self.sleep_state:
                    continue
                self.last_user_text = None
                self.last_bot_text = self._pending_sleep_message
                self.set_post_speech_state(self.sleep_state)
                self._clear_transcripts()
                self.arm_sleep_guard(settings.SLEEP_ENTRY_GUARD)
                self.clear_wake_events()
                if self.current_state is not self.speaking_state:
                    self.set_state(self.speaking_state)
                    transitioned = True
                continue

            if event.event_type == WakeEventType.SATISFIED:
                if self.current_state is self.sleep_state:
                    continue
                self.last_user_text = None
                self.last_bot_text = self._satisfaction_confirmation
                self.set_post_speech_state(self.sleep_state)
                self._clear_transcripts()
                self.arm_sleep_guard(settings.SLEEP_ENTRY_GUARD)
                self.clear_wake_events()
                if self.current_state is not self.speaking_state:
                    self.set_state(self.speaking_state)
                    transitioned = True
                continue

            if self.current_state is not self.sleep_state:
                self.last_user_text = None
                self.last_bot_text = None
                self.arm_sleep_guard(settings.SLEEP_ENTRY_GUARD)
                self.clear_wake_events()
                self.set_state(self.sleep_state)
                transitioned = True

        return transitioned

    def _clear_transcripts(self) -> None:
        with self._event_lock:
            self._transcript_events.clear()

    def _mark_awake(self) -> None:
        now = time.time()
        self._last_awake_ts = now
        self._last_user_activity_ts = now

    def _mark_sleep(self) -> None:
        self._last_awake_ts = time.time()
