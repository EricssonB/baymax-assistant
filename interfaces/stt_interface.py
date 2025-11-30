from abc import ABC, abstractmethod
from typing import Optional

class STTInterface(ABC):
    """Interface for speech-to-text services (Deepgram, Whisper, etc)."""

    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes) -> Optional[str]:
        """Convert raw audio bytes into text."""
        pass
