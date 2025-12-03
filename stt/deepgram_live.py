"""Deepgram streaming interface for Baymax 2.0."""

from __future__ import annotations

import json
import string
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, cast

from config_app.settings import settings
from core.events import TranscriptEvent, WakeEvent, WakeEventType

try:
    from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
except Exception as exc:  # pragma: no cover - import guard
    DeepgramClient = None  # type: ignore
    LiveOptions = None  # type: ignore
    LiveTranscriptionEvents = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

if TYPE_CHECKING:
    from deepgram import LiveOptions as LiveOptionsType
else:  # pragma: no cover - runtime fallback for typing
    LiveOptionsType = Any


WakeCallback = Callable[[WakeEvent], None]
TranscriptCallback = Callable[[TranscriptEvent], None]
ErrorCallback = Callable[[Exception], None]


WAKE_WORDS = (
    "hey baymax",
    "hi baymax",
    "hello baymax",
    "baymax",
    "hey bay max",
    "hi bay max",
    "hello bay max",
    "hey baymex",
    "hi baymex",
    "hello baymex",
    "baymex",
    "hey bemax",
    "hi bemax",
    "hello bemax",
    "bemax",
    "hey bemex",
    "hi bemex",
    "hello bemex",
    "bemex",
)

SLEEP_WORDS = (
    "bye baymax",
    "goodbye baymax",
    "good bye baymax",
    "goodnight baymax",
    "good night baymax",
    "bye bay max",
    "goodbye bay max",
    "good bye bay max",
    "goodnight bay max",
    "good night bay max",
    "sleep baymax",
    "go to sleep baymax",
    "goodnight",
    "good night",
    "see you later baymax",
    "bye baymex",
    "goodbye baymex",
    "good bye baymex",
    "goodnight baymex",
    "good night baymex",
    "sleep baymex",
    "go to sleep baymex",
    "bye bemax",
    "goodbye bemax",
    "good bye bemax",
    "goodnight bemax",
    "good night bemax",
    "sleep bemax",
    "go to sleep bemax",
    "bye bemex",
    "goodbye bemex",
    "good bye bemex",
    "goodnight bemex",
    "good night bemex",
    "sleep bemex",
    "go to sleep bemex",
)

SATISFACTION_PHRASES = (
    "you are satisfied with my care",
    "i am satisfied with your care",
    "satisfied with your care",
    "satisfied with my care",
    "i'm satisfied with your care",
    "satisfied with care",
    "satisfied",
    "yes i am satisfied",
)


_PUNCT_TABLE = str.maketrans({char: " " for char in string.punctuation})


def _normalize(text: str) -> str:
    collapsed = text.lower().translate(_PUNCT_TABLE)
    return " ".join(collapsed.split())


def _contains_phrase(text: str, phrases) -> bool:
    normalized = _normalize(text)
    return any(phrase in normalized for phrase in phrases)


def _should_process_transcript(transcript: str) -> bool:
    words = transcript.split()
    if not words:
        return False

    ends_with_punctuation = transcript.rstrip().endswith((".", "!", "?"))
    min_words = max(getattr(settings, "MIN_TRANSCRIPT_WORDS", 2), 1)

    if len(words) >= min_words:
        return True

    # Allow a single emphasized word when Deepgram already marked it final
    if ends_with_punctuation and len(words) == 1:
        return True

    return False


def _to_dict_safe(obj: Any) -> Optional[dict]:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            data = obj.to_dict()
            if isinstance(data, dict):
                return data
        except Exception:
            return None
    if hasattr(obj, "to_json"):
        try:
            data = json.loads(obj.to_json())
            if isinstance(data, dict):
                return data
        except Exception:
            return None
    return None


class DeepgramStreamingService:
    """Wraps Deepgram's websocket client and exposes Baymax-friendly callbacks."""

    def __init__(
        self,
        microphone,
        *,
        live_options: Optional[LiveOptionsType] = None,
        min_time_between_responses: float = 3.0,
    ) -> None:
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is missing in .env")

        if DeepgramClient is None or LiveOptions is None or LiveTranscriptionEvents is None:  # pragma: no cover - import guard
            raise ImportError(
                "Deepgram SDK is not available" + (f": {_IMPORT_ERROR}" if _IMPORT_ERROR else "")
            )

        self.microphone = microphone
        self._client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        self._connection: Any = None
        self._sender_thread: Optional[threading.Thread] = None
        self._sending = threading.Event()
        self._tts_playing = threading.Event()
        self._last_response_ts = 0.0
        self._min_time_between_responses = max(min_time_between_responses, 0.0)
        self._events = LiveTranscriptionEvents

        # Callbacks
        self._wake_listeners: List[WakeCallback] = []
        self._transcript_listeners: List[TranscriptCallback] = []
        self._error_listeners: List[ErrorCallback] = []

        sample_rate = getattr(microphone, "sample_rate", 16000)
        channels = getattr(microphone, "channels", 1)

        endpoint_window = str(max(settings.DEEPGRAM_ENDPOINT_MS, 0))

        self._options = live_options or LiveOptions(
            model="nova-2",
            punctuate=True,
            interim_results=True,
            smart_format=True,
            encoding="linear16",
            channels=channels,
            sample_rate=sample_rate,
            endpointing=endpoint_window,
        )

    # ------------------------------------------------------------------
    # Callback registration helpers
    # ------------------------------------------------------------------
    def add_wake_listener(self, callback: WakeCallback) -> None:
        self._wake_listeners.append(callback)

    def add_transcript_listener(self, callback: TranscriptCallback) -> None:
        self._transcript_listeners.append(callback)

    def add_error_listener(self, callback: ErrorCallback) -> None:
        self._error_listeners.append(callback)

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._connection is not None:
            return

        connection = self._open_connection_with_retry()
        if connection is None:
            raise RuntimeError("Unable to establish Deepgram streaming connection")

        self._connection = connection

        self.microphone.start_stream()
        self._sending.set()
        self._sender_thread = threading.Thread(target=self._stream_audio, name="DG-AudioStreamer", daemon=True)
        self._sender_thread.start()

    def stop(self) -> None:
        self._sending.clear()
        self._tts_playing.clear()

        if self._sender_thread and self._sender_thread.is_alive():
            self._sender_thread.join(timeout=1.0)
        self._sender_thread = None

        try:
            self.microphone.stop_stream()
        except Exception as exc:  # pragma: no cover - defensive stop
            self._emit_error(exc)

        if self._connection is not None:
            try:
                self._connection.finish()  # type: ignore[attr-defined]
            except Exception as exc:  # pragma: no cover - defensive stop
                self._emit_error(exc)
            finally:
                self._connection = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _stream_audio(self) -> None:
        consecutive_failures = 0
        while self._sending.is_set():
            try:
                chunk = self.microphone.read_audio_chunk()
            except Exception as exc:  # pragma: no cover - audio failure
                self._emit_error(exc)
                time.sleep(0.05)
                continue

            if not chunk:
                time.sleep(0.01)
                continue

            chunk = self._mute_chunk_if_needed(chunk)

            if self._connection is None:
                if not self._reconnect_stream():
                    time.sleep(0.5)
                    continue

            try:
                if self._connection is not None:
                    self._connection.send(chunk)  # type: ignore[attr-defined]
                consecutive_failures = 0
            except Exception as exc:  # pragma: no cover - network failure
                self._emit_error(exc)
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    if self._reconnect_stream():
                        consecutive_failures = 0
                    else:
                        time.sleep(0.5)
                        self._connection = None
                        consecutive_failures = 0
                else:
                    time.sleep(0.05)

        consecutive_failures = 0

    def _open_connection_with_retry(self) -> Optional[Any]:
        attempts: Tuple[float, float, float] = (0.0, 1.0, 3.0)
        last_error: Optional[Exception] = None

        for delay in attempts:
            if delay:
                time.sleep(delay)

            connection: Optional[Any] = None
            try:
                # Deepgram SDK v3 exposes streaming via `listen.live`
                connection = cast(Any, self._client.listen.live.v("1"))
                connection.on(  # type: ignore[attr-defined]
                    self._events.Transcript, self._handle_transcript
                )
                connection.on(  # type: ignore[attr-defined]
                    self._events.Error, self._handle_connection_error
                )
                connection.start(self._options)  # type: ignore[attr-defined]
                return connection
            except Exception as exc:  # pragma: no cover - network setup
                last_error = exc
                self._emit_error(exc)
                if connection is not None:
                    try:
                        connection.finish()  # type: ignore[attr-defined]
                    except Exception:
                        pass

        if last_error:
            self._emit_error(last_error)

        return None

    def _reconnect_stream(self) -> bool:
        print("[STT] Attempting to reconnect Deepgram stream...")
        connection = self._open_connection_with_retry()
        if connection is None:
            print("[STT] Reconnection failed")
            return False

        self._connection = connection
        print("[STT] Reconnected to Deepgram")
        return True

    def _handle_transcript(self, *_args, **kwargs) -> None:  # pragma: no cover - callback path
        if "result" in kwargs:
            result = kwargs["result"]
        elif len(_args) >= 2:
            result = _args[1]
        elif len(_args) == 1:
            result = _args[0]
        else:
            return

        if result is None:
            return

        result_dict = _to_dict_safe(result) or {}

        channel_dict = _to_dict_safe(getattr(result, "channel", None))
        if channel_dict is None and result_dict:
            raw_channel = result_dict.get("channel")
            channel_dict = raw_channel if isinstance(raw_channel, dict) else _to_dict_safe(raw_channel)

        alternatives: List[Any] = []

        if channel_dict and isinstance(channel_dict, dict):
            raw_alts = channel_dict.get("alternatives")
            if isinstance(raw_alts, list):
                alternatives = raw_alts

        if not alternatives:
            channel_obj = getattr(result, "channel", None)
            raw_alts = getattr(channel_obj, "alternatives", None) if channel_obj is not None else None
            if isinstance(raw_alts, list):
                alternatives = raw_alts

        transcript = ""
        if alternatives:
            first_alt = alternatives[0]
            alt_dict = _to_dict_safe(first_alt)
            if alt_dict:
                transcript = (alt_dict.get("transcript") or "").strip()
            elif isinstance(first_alt, dict):
                transcript = (first_alt.get("transcript") or "").strip()
            else:
                transcript = (getattr(first_alt, "transcript", "") or "").strip()

        if not transcript:
            return

        is_final = bool(result_dict.get("is_final")) if result_dict else bool(getattr(result, "is_final", False))

        if is_final:
            self._process_final_transcript(transcript, raw=result)
        else:
            event = TranscriptEvent(text=transcript, is_final=False, should_process=False, raw=result)
            self._emit_transcript(event)

    def _process_final_transcript(self, transcript: str, raw) -> None:
        has_satisfaction = _contains_phrase(transcript, SATISFACTION_PHRASES)
        has_sleep = _contains_phrase(transcript, SLEEP_WORDS)
        has_wake = _contains_phrase(transcript, WAKE_WORDS)

        if has_satisfaction:
            self._emit_wake(WakeEventType.SATISFIED, transcript)

        if has_sleep:
            self._emit_wake(WakeEventType.SLEEP, transcript)

        if has_wake and not (has_sleep or has_satisfaction):
            self._emit_wake(WakeEventType.WAKE, transcript)

        event = TranscriptEvent(
            text=transcript,
            is_final=True,
            should_process=_should_process_transcript(transcript),
            raw=raw,
        )
        self._emit_transcript(event)

    def _handle_connection_error(self, *_args, **kwargs) -> None:  # pragma: no cover - callback path
        if "error" in kwargs:
            error = kwargs["error"]
        elif len(_args) >= 2:
            error = _args[1]
        elif len(_args) == 1:
            error = _args[0]
        else:
            error = Exception("Unknown streaming error")

        exc = error if isinstance(error, Exception) else Exception(str(error))
        self._emit_error(exc)

    def _emit_wake(self, event_type: WakeEventType, transcript: str) -> None:
        event = WakeEvent(event_type=event_type, transcript=transcript)
        for callback in list(self._wake_listeners):
            try:
                callback(event)
            except Exception as exc:  # pragma: no cover - listener failure
                self._emit_error(exc)

    def _emit_transcript(self, event: TranscriptEvent) -> None:
        for callback in list(self._transcript_listeners):
            try:
                callback(event)
            except Exception as exc:  # pragma: no cover - listener failure
                self._emit_error(exc)

    def _emit_error(self, exc: Exception) -> None:
        if not self._error_listeners:
            print("[STT] Streaming error:", exc)
            return

        for callback in list(self._error_listeners):
            try:
                callback(exc)
            except Exception as listener_exc:  # pragma: no cover - listener failure
                print("[STT] Error listener raised:", listener_exc)

    # ------------------------------------------------------------------
    # Speaking coordination helpers
    # ------------------------------------------------------------------
    def set_speaking(self, is_speaking: bool) -> None:
        if is_speaking:
            self._tts_playing.set()
        else:
            self._tts_playing.clear()

    def notify_response_sent(self, duration: float = 0.0, *, buffer_override: Optional[float] = None) -> None:
        """Signal that TTS playback finished; apply the safety buffer before unmuting."""
        buffer = settings.TTS_POST_BUFFER if buffer_override is None else max(buffer_override, 0.0)
        buffer = max(buffer, 0.0)
        # Playback already consumed `duration`, so only keep the short safety buffer.
        self._mute_until_ts = time.time() + buffer

    def _mute_chunk_if_needed(self, chunk: bytes) -> bytes:
        if not chunk:
            return chunk

        if self._tts_playing.is_set():
            return b"\x00" * len(chunk)

        if time.time() < getattr(self, "_mute_until_ts", 0.0):
            return b"\x00" * len(chunk)

        return chunk