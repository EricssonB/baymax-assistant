from typing import Optional
from interfaces.stt_interface import STTInterface
from config.settings import settings

class DeepgramSTT(STTInterface):
    """Deepgram implementation of the speech-to-text interface (safe skeleton)."""

    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is missing in .env")

        # Lazy import: ensures no crash during global import
        try:
            from deepgram import DeepgramClient
            self.client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        except Exception as e:
            print("[Deepgram] Warning: Deepgram SDK not available:", e)
            self.client = None

    def transcribe_audio(self, audio_bytes: bytes) -> Optional[str]:
        """
        Placeholder implementation.
        TODO: Add real Deepgram streaming or synchronous transcription.
        """
        print("[Deepgram] transcribe_audio() called. Bytes length:", len(audio_bytes))

        # Return None to indicate no transcription (skeleton)
        return None
