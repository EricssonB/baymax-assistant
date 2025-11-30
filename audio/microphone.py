from interfaces.audio_interface import AudioInterface

class Microphone(AudioInterface):
    """Microphone input system (clean skeleton, no hardware dependencies)."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

    def start_stream(self):
        """Placeholder: Start microphone streaming."""
        print("[Audio] Starting microphone stream (skeleton).")

    def read_audio_chunk(self) -> bytes:
        """
        Placeholder: returns silence.
        TODO: Replace with actual audio input using sounddevice on real hardware.
        """
        print("[Audio] read_audio_chunk() called.")
        return b""

    def stop_stream(self):
        """Placeholder: Stop microphone streaming."""
        print("[Audio] Stopping microphone stream (skeleton).")
