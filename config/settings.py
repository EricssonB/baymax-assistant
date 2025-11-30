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

        # Optional: add future settings here
        self.SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))

# Create a single shared instance
settings = Settings()
