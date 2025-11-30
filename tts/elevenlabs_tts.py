from interfaces.tts_interface import TTSInterface
from config.settings import settings
import os
from elevenlabs.client import ElevenLabs

class ElevenLabsTTS(TTSInterface):
    """ElevenLabs TTS using Baymax voice settings."""

    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is missing in .env")

        try:
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        except Exception as e:
            print("[ElevenLabs TTS] SDK import error:", e)
            self.client = None

        # ⭐ Your Baymax voice
        self.voice_id = "J74irub9nJ8NIWEDskLz"
        self.model_id = "eleven_multilingual_v2"

        self.output_path = "audio/output.wav"
        os.makedirs("audio", exist_ok=True)

    def speak(self, text: str) -> None:
        if not self.client:
            print("[ElevenLabs TTS] No client available.")
            return

        print("[ElevenLabs TTS] Generating speech for:", text)

        try:
            # ⭐ SAME SETTINGS from your working Baymax script
            audio_stream = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id=self.model_id,
                text=text,
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": 0.8
                }
            )

            # Save audio to file (your architecture requires writing to WAV)
            with open(self.output_path, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)

            print("[ElevenLabs TTS] Saved WAV to", self.output_path)

        except Exception as e:
            print("[ElevenLabs TTS] Error generating audio:", e)
