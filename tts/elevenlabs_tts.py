import os
import time
import wave
from typing import Iterable, Iterator, Optional, Tuple, Union

from config_app.settings import settings
from interfaces.tts_interface import TTSInterface
from elevenlabs import ElevenLabs


class ElevenLabsTTS(TTSInterface):
    """ElevenLabs TTS using Baymax voice settings."""

    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is missing in .env")

        try:
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        except Exception as e:
            print("[TTS] SDK import error:", e)
            self.client = None

        # ⭐ Your Baymax voice
        self.voice_id = "J74irub9nJ8NIWEDskLz"
        self.model_id = "eleven_multilingual_v2"
        self.output_format = "pcm_16000"
        self.optimize_streaming_latency = 3  # Max optimization for lowest latency
        self.sample_rate = 16000
        self.num_channels = 1
        self.sample_width = 2  # bytes per sample for 16-bit PCM

        self.output_path = "audio/output.wav"
        os.makedirs("audio", exist_ok=True)

        self._last_duration: float = 0.0

    @property
    def last_duration(self) -> float:
        """Return the duration (seconds) of the most recently generated audio."""
        return self._last_duration

    def speak(self, text: str) -> None:
        """Convert `text` into speech and persist the PCM stream as a WAV file."""
        if not self.client:
            print("[TTS] No client available.")
            return

        print("[TTS] Generating speech...")

        response = self._request_audio(text)
        if response is None:
            print("[TTS] Failed to fetch audio after retries.")
            return

        try:
            with wave.open(self.output_path, "wb") as wav_file:
                wav_file.setnchannels(self.num_channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)

                for chunk in self._iterate_audio_chunks(response):
                    if not chunk:
                        continue
                    wav_file.writeframes(chunk)

            print(f"[TTS] Saved WAV -> {self.output_path}")
            self._last_duration = self._compute_wav_duration(self.output_path)
        except Exception as e:
            print("[TTS] Error writing audio:", e)
            self._last_duration = 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _compute_wav_duration(self, path: str) -> float:
        """Return duration in seconds of a WAV file."""
        try:
            with wave.open(path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return frames / rate
        except Exception:
            pass
        return 0.0

    def _iterate_audio_chunks(self, payload: Iterable[Union[bytes, dict]]) -> Iterator[bytes]:
        """Normalize ElevenLabs streaming payloads into raw byte chunks."""
        for chunk in payload:
            if isinstance(chunk, bytes):
                yield chunk
                continue

            if isinstance(chunk, dict):
                audio_bytes = chunk.get("audio")
                if isinstance(audio_bytes, bytes):
                    yield audio_bytes
                continue

            # Some client builds yield objects with a .audio attribute
            audio_attr = getattr(chunk, "audio", None)
            if isinstance(audio_attr, bytes):
                yield audio_attr

    def _request_audio(self, text: str) -> Optional[Iterable[Union[bytes, dict]]]:
        """Fetch streaming audio frames, retrying on transient API failures."""
        client = self.client
        if client is None:
            return None

        attempts: Tuple[float, float] = (0.0, 0.3)  # Faster retries
        last_error: Optional[Exception] = None

        for delay in attempts:
            if delay:
                time.sleep(delay)

            try:
                return client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    model_id=self.model_id,
                    text=text,
                    output_format=self.output_format,
                    optimize_streaming_latency=self.optimize_streaming_latency,
                    voice_settings={
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "speed": 0.8,
                    },  # type: ignore[arg-type]
                )
            except Exception as exc:
                last_error = exc
                print(f"[TTS] ElevenLabs request failed (retrying): {exc}")

        if last_error:
            print("[TTS] Exhausted ElevenLabs retries:", last_error)

        return None
