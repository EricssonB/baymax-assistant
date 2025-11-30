import sounddevice as sd
import wave
from typing import Optional

from config.settings import settings
from interfaces.audio_interface import AudioInterface


class Microphone(AudioInterface):
    """Real microphone input using sounddevice."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: Optional[int] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunk_size = chunk_size or settings.CHUNK_SIZE
        self._stream = None

    def start_stream(self):
        """Start a streaming audio capture session."""
        if self._stream:
            return

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self._chunk_size
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            print("[Audio] Failed to start microphone stream:", exc)

    def read_audio_chunk(self) -> bytes:
        """Read a chunk from the active stream (starts stream if needed)."""
        if not self._stream:
            self.start_stream()

        if not self._stream:
            return b""

        try:
            frames, _ = self._stream.read(self._chunk_size)
            return frames.tobytes()
        except Exception as exc:
            print("[Audio] Failed to read audio chunk:", exc)
            return b""

    def stop_stream(self):
        """Stop and dispose of the active stream."""
        if not self._stream:
            return

        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            print("[Audio] Failed to stop microphone stream:", exc)
        finally:
            self._stream = None

    def record_to_file(self, filename: str, duration: int = 3):
        """Record audio from the microphone and save as a WAV file."""
        print(f"[Audio] Recording {duration}s to {filename}...")

        try:
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16"
            )
            sd.wait()  # Block until recording finishes

            # Save WAV
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # int16 → 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio.tobytes())

            print(f"[Audio] Saved recording to {filename}")

        except Exception as e:
            print("[Audio] Microphone error:", e)
