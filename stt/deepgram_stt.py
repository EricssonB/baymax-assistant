from typing import Any, Optional

import json

from interfaces.stt_interface import STTInterface
from config_app.settings import settings


class DeepgramSTT(STTInterface):
    """Deepgram prerecorded transcription helper using SDK v3."""

    def __init__(self) -> None:
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is missing in .env")

        self._client = None
        self._options_cls = None

        try:
            from deepgram import DeepgramClient, PrerecordedOptions

            self._client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
            self._options_cls = PrerecordedOptions
        except Exception as exc:  # pragma: no cover - optional dependency guard
            print("[STT] SDK import error:", exc)

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Convert in-memory WAV bytes to text."""
        if not self._client or not self._options_cls:
            print("[STT] No client available.")
            return ""

        if not audio_bytes:
            return ""

        try:
            options = self._options_cls(
                model="nova-2",
                smart_format=True,
            )

            source = {"buffer": audio_bytes, "mimetype": "audio/wav"}

            response = self._client.listen.prerecorded.v("1").transcribe_file(  # type: ignore[attr-defined]
                source,
                options,
            )

            transcript = _extract_transcript(response)
            if transcript:
                print(f"[STT] Transcript -> {transcript}")
            else:
                print("[STT] No transcript in response")
            return transcript
        except Exception as exc:
            print("[STT] Error:", exc)
            return ""

    def transcribe(self, audio_path: str) -> str:
        try:
            with open(audio_path, "rb") as wav_file:
                audio_bytes = wav_file.read()
        except Exception as exc:
            print("[STT] Failed to read audio file:", exc)
            return ""

        return self.transcribe_audio(audio_bytes)


def _extract_transcript(response: Optional[Any]) -> str:
    """Safely traverse Deepgram's nested response payload."""
    if response is None:
        return ""

    if hasattr(response, "to_dict"):
        try:
            response = response.to_dict()
        except Exception:
            return ""
    elif hasattr(response, "to_json"):
        try:
            response = json.loads(response.to_json())
        except Exception:
            return ""

    if not isinstance(response, dict):
        return ""

    try:
        channels = response["results"]["channels"]
        if not channels:
            return ""
        alternatives = channels[0]["alternatives"]
        if not alternatives:
            return ""
        transcript = alternatives[0].get("transcript", "")
        return transcript or ""
    except (KeyError, IndexError, TypeError):
        return ""
