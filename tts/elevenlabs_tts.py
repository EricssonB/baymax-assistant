from interfaces.tts_interface import TTSInterface
from config.settings import settings

class ElevenLabsTTS(TTSInterface):
    """ElevenLabs TTS engine (safe architecture skeleton)."""

    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is missing in .env")

        # Lazy import protects against missing dependencies
        try:
            from elevenlabs import ElevenLabs
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        except Exception as e:
            print("[ElevenLabs TTS] Warning: ElevenLabs SDK not available:", e)
            self.client = None

        # Placeholder voice/model selection (will be configurable later)
        self.voice = "Baymax"

    def speak(self, text: str) -> None:
        """
        Placeholder implementation.
        TODO: Replace with actual audio generation + playback.
        """
        print(f"[ElevenLabs TTS] speak() called with text: {text}")

        # No real API call yet — architecture-only
        return None
