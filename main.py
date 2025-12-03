import os
import subprocess
import threading
import time
from dotenv import load_dotenv

from audio.microphone import Microphone
from config_app.settings import settings
from stt.deepgram_stt import DeepgramSTT

try:
    from stt.deepgram_live import DeepgramStreamingService
except Exception:  # pragma: no cover - optional dependency
    DeepgramStreamingService = None  # type: ignore
from llm.openai_llm import OpenAILLM
from tts.elevenlabs_tts import ElevenLabsTTS
from app_states.state_manager import StateManager
from core.idle_monitor import IdleMonitor
from wakeword.wakeword_detector import WakeWordDetector

# Load .env variables
load_dotenv()

# Pre-cached startup audio path
_STARTUP_AUDIO = "audio/startup_initializing.wav"


def _play_startup_audio(tts: ElevenLabsTTS) -> None:
    """Play cached startup audio, generating it once if missing."""
    if not os.path.exists(_STARTUP_AUDIO):
        # Generate and cache on first run
        tts.speak("Initializing")
        if os.path.exists(tts.output_path):
            os.rename(tts.output_path, _STARTUP_AUDIO)

    if os.path.exists(_STARTUP_AUDIO):
        subprocess.run(["afplay", _STARTUP_AUDIO], check=False)


def _announce_system_online(tts: ElevenLabsTTS, stt_stream) -> None:
    """Speak a readiness announcement without leaving the state machine."""
    try:
        if stt_stream:
            stt_stream.set_speaking(True)

        tts.speak("System online.")
        output_path = getattr(tts, "output_path", "audio/output.wav")
        duration = getattr(tts, "last_duration", 0.0)

        if os.path.exists(output_path):
            subprocess.run(["afplay", output_path], check=False)

        if stt_stream:
            stt_stream.set_speaking(False)
            # Drop the buffer so the wake word can be heard immediately after boot.
            stt_stream.notify_response_sent(duration, buffer_override=0.0)
            if duration:
                # Allow macOS audio to settle while unmuted.
                time.sleep(0.05)
    except Exception as exc:
        print("[Startup] System online announcement failed:", exc)

def _validate_environment() -> None:
    """Fail fast if required API keys are absent."""
    required = (
        ("DEEPGRAM_API_KEY", settings.DEEPGRAM_API_KEY),
        ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
        ("ELEVENLABS_API_KEY", settings.ELEVENLABS_API_KEY),
    )

    missing = [name for (name, value) in required if not value]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {joined}")


def main():
    print("\n=== Baymax 2.0 – Starting Assistant ===")

    _validate_environment()

    # Initialize core modules
    mic = Microphone()
    stt = DeepgramSTT()
    llm = OpenAILLM()
    tts = ElevenLabsTTS()
    wake = WakeWordDetector(
        energy_threshold=settings.WAKE_ENERGY_THRESHOLD,
        required_hits=settings.WAKE_REQUIRED_HITS,
        debug_interval=settings.WAKE_DEBUG_INTERVAL,
    )

    # Play startup announcement in background while we set up streaming
    startup_thread = threading.Thread(target=_play_startup_audio, args=(tts,), daemon=True)
    startup_thread.start()

    # Streaming Deepgram service (starts in parallel with audio playback)
    stt_stream = None
    idle_monitor = None
    if DeepgramStreamingService is not None:
        try:
            stt_stream = DeepgramStreamingService(microphone=mic)
            stt_stream.start()
        except Exception as exc:
            print("[STT] Streaming unavailable:", exc)
            stt_stream = None

    # Initialize StateManager with all modules
    manager = StateManager(
        mic=mic,
        stt=stt,
        tts=tts,
        wake=wake,
        llm=llm,
        stt_stream=stt_stream
    )

    if stt_stream:
        idle_monitor = IdleMonitor(manager=manager)
        idle_monitor.start()

    # Wait for startup audio to finish before entering main loop
    startup_thread.join()

    _announce_system_online(tts, stt_stream)

    # Start in SleepState – Baymax waits for wake phrase
    manager.set_state(manager.sleep_state)

    print("\n=== Baymax 2.0 – Ready (say 'Hey Baymax' to wake) ===")

    # Main loop
    try:
        while True:
            manager.update()
    except KeyboardInterrupt:
        print("\n=== Baymax 2.0 – Shutting down ===")
    finally:
        if stt_stream:
            stt_stream.stop()
        if idle_monitor:
            idle_monitor.stop()

if __name__ == "__main__":
    main()
