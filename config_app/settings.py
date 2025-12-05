from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Centralized configuration for Baymax.
    All API keys and environment-based settings live here.
    """

    def __init__(self):
        self.DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
        self.ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "J74irub9nJ8NIWEDskLz")

        # Optional: add future settings here
        self.SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))
        self.WAKE_ENERGY_THRESHOLD = int(os.getenv("WAKE_ENERGY_THRESHOLD", 220))
        self.WAKE_REQUIRED_HITS = int(os.getenv("WAKE_REQUIRED_HITS", 2))
        self.WAKE_DEBUG_INTERVAL = float(os.getenv("WAKE_DEBUG_INTERVAL", 0.0))
        self.TTS_POST_BUFFER = float(os.getenv("TTS_POST_BUFFER", 0.05))
        self.DEEPGRAM_ENDPOINT_MS = int(os.getenv("DEEPGRAM_ENDPOINT_MS", 200))
        self.MIN_TRANSCRIPT_WORDS = int(os.getenv("MIN_TRANSCRIPT_WORDS", 2))
        self.SLEEP_ENTRY_GUARD = float(os.getenv("SLEEP_ENTRY_GUARD", 0.6))

# Create a single shared instance
settings = Settings()
