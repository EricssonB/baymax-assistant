from abc import ABC, abstractmethod

class AudioInterface(ABC):
    """Interface for audio input systems."""

    @abstractmethod
    def start_stream(self):
        """Start the audio stream."""
        pass

    @abstractmethod
    def read_audio_chunk(self) -> bytes:
        """Read an audio chunk and return raw bytes."""
        pass

    @abstractmethod
    def stop_stream(self):
        """Stop the audio stream."""
        pass
