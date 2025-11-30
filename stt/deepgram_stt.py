from typing import Optional

from interfaces.stt_interface import STTInterface
from config.settings import settings

class DeepgramSTT(STTInterface):
    """Real Deepgram STT using the official Python SDK."""

    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is missing in .env")

        self.DeepgramClient = None
        self.PrerecordedOptions = None

        try:
            from deepgram import DeepgramClient, PrerecordedOptions
            self.DeepgramClient = DeepgramClient
            self.PrerecordedOptions = PrerecordedOptions
        except Exception as e:
            print("[Deepgram STT] SDK import error:", e)

        self.client = None
        if self.DeepgramClient:
            try:
                self.client = self.DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
            except Exception as e:
                print("[Deepgram STT] Client init error:", e)

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Convert in-memory audio bytes to text."""
        if not self.client or not self.PrerecordedOptions:
            print("[Deepgram STT] No client available.")
            return ""

        if not audio_bytes:
            return ""

        try:
            options = self.PrerecordedOptions(
                model="nova-2",
                smart_format=True
            )

            response = self.client.listen.prerecorded.v("1").transcribe_file(
                source={"buffer": audio_bytes},
                options=options
            )

            transcript = (
                response["results"]["channels"][0]["alternatives"][0]["transcript"]
            )

            print("[Deepgram STT] Transcript:", transcript)
            return transcript

        except Exception as e:
            print("[Deepgram STT] Error:", e)
            return ""

    def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file synchronously."""
        try:
            with open(audio_path, "rb") as file:
                audio_bytes = file.read()
        except Exception as e:
            print("[Deepgram STT] Failed to read audio file:", e)
            return ""

        return self.transcribe_audio(audio_bytes)
