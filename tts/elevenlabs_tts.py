import os
import time
import wave
from typing import Iterator, Optional

from config_app.settings import settings
from interfaces.tts_interface import TTSInterface
import requests


class ElevenLabsTTS(TTSInterface):
    """ElevenLabs TTS using Baymax voice settings."""

    def __init__(self):
        api_key = settings.ELEVENLABS_API_KEY
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is missing in .env")

        self._session = requests.Session()
        self._api_key = api_key

        # ⭐ Your Baymax voice
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = "eleven_multilingual_v2"
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
        finally:
            response.close()

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

    def _iterate_audio_chunks(self, response: requests.Response) -> Iterator[bytes]:
        """Stream PCM chunks from the ElevenLabs HTTP response."""
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                yield chunk

    def _request_audio(self, text: str) -> Optional[requests.Response]:
        """Fetch streaming audio frames, retrying on transient API failures."""
        attempts = (0.0, 0.3)
        last_error: Optional[Exception] = None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        payload = {
            "text": text,
            "model_id": self.model_id,
            "optimize_streaming_latency": self.optimize_streaming_latency,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "speed": 0.8,
            },
        }
        headers = {
            "xi-api-key": self._api_key,
            "Accept": "audio/pcm",
        }
        params = {
            "output_format": f"pcm_{self.sample_rate}",
        }

        for delay in attempts:
            if delay:
                time.sleep(delay)

            try:
                response = self._session.post(
                    url,
                    json=payload,
                    headers=headers,
                    params=params,
                    stream=True,
                    timeout=30,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                print(f"[TTS] ElevenLabs request failed (retrying): {exc}")

        if last_error:
            print("[TTS] Exhausted ElevenLabs retries:", last_error)

        return None
