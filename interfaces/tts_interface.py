from abc import ABC, abstractmethod

class TTSInterface(ABC):
    """Interface for text-to-speech engines."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Convert text to speech and play the audio."""
        pass
