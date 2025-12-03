import time
import numpy as np
import sounddevice as sd
import wave
from typing import Optional

from config_app.settings import settings
from interfaces.audio_interface import AudioInterface


def _current_time() -> float:
    return time.time()


class Microphone(AudioInterface):
    """Real microphone input using sounddevice."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: Optional[int] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunk_size = chunk_size or settings.CHUNK_SIZE
        self._stream = None
        self._mute_until: float = 0.0

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

    def mute_for(self, duration: float) -> None:
        """Temporarily suppress capture for the given duration in seconds."""
        self._mute_until = max(self._mute_until, _current_time() + max(duration, 0.0))

    def read_audio_chunk(self) -> bytes:
        """Read a chunk from the active stream (starts stream if needed)."""
        if not self._stream:
            self.start_stream()

        if not self._stream:
            return b""

        if _current_time() < self._mute_until:
            time.sleep(0.05)
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
        """Record audio with early stop on silence detection."""
        print(f"[Audio] Recording up to {duration}s -> {filename}")

        wait_timeout = max(self._mute_until - _current_time(), 0.0)
        if wait_timeout > 0:
            time.sleep(wait_timeout)

        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(chunk_duration * self.sample_rate)
        max_chunks = int(duration / chunk_duration)
        silence_threshold = 50  # Very low RMS threshold for quiet mics
        silence_chunks_to_stop = 12  # Stop after 1.2s of silence (after speech detected)
        min_speech_chunks = 5  # Require at least 0.5s of speech before allowing early stop
        
        all_audio = []
        speech_chunks = 0
        consecutive_silence = 0

        try:
            for _ in range(max_chunks):
                chunk = sd.rec(
                    chunk_samples,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="int16"
                )
                sd.wait()
                all_audio.append(chunk)
                
                # Calculate RMS volume
                rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                print(f"[Audio] RMS: {rms:.0f}")
                
                if rms > silence_threshold:
                    speech_chunks += 1
                    consecutive_silence = 0
                elif speech_chunks >= min_speech_chunks:
                    consecutive_silence += 1
                    if consecutive_silence >= silence_chunks_to_stop:
                        print("[Audio] Silence detected, stopping early")
                        break

            # Combine all chunks
            audio = np.concatenate(all_audio)

            # Save WAV
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # int16 → 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio.tobytes())

            actual_duration = len(audio) / self.sample_rate
            print(f"[Audio] Saved recording ({actual_duration:.1f}s) -> {filename}")

        except Exception as e:
            print("[Audio] Microphone error:", e)
