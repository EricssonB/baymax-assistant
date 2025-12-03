import subprocess
import time

from interfaces.state_interface import State

def _play_ready_beep():
    """Play a short beep to indicate Baymax is listening."""
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Pop.aiff"], check=False)
    except Exception:
        pass

class ListeningState(State):

    def __init__(self, mic=None, stt=None):
        self.mic = mic
        self.stt = stt
        self._waiting_logged = False

    def on_enter(self):
        print("[State] >>> ListeningState")
        self._waiting_logged = False

    def on_exit(self):
        print("[State] <<< ListeningState")
        self._waiting_logged = False

    def handle(self, manager, user_input):
        if manager.streaming_enabled:
            transcript = manager.consume_transcript()

            if transcript:
                print(f"[ListeningState] Transcript -> {transcript}")
                self._waiting_logged = False
                return manager.processing_state

            if not self._waiting_logged:
                print("[ListeningState] Waiting for transcript...")
                self._waiting_logged = True

            time.sleep(0.1)
            return None

        print(f"[ListeningState] Handling: {user_input}")

        if not self.mic:
            print("[ListeningState] No microphone instance!")
            return manager.idle_state

        if hasattr(manager, "speaking_cooldown_active") and manager.speaking_cooldown_active():
            wait = manager.speaking_cooldown_remaining()
            if wait > 0:
                print(f"[ListeningState] Waiting {wait:.2f}s to avoid echo...")
                time.sleep(wait)

        # Record audio to a fixed scratch file
        audio_path = "audio/input.wav"

        _play_ready_beep()
        time.sleep(0.3)

        print("[ListeningState] Recording... speak now!")
        self.mic.record_to_file(audio_path, duration=5)

        # Transcribe
        print("[ListeningState] Transcribing...")
        transcript = ""
        if self.stt:
            transcript = self.stt.transcribe(audio_path)
            if not transcript:
                print("[ListeningState] No transcript captured.")
            else:
                manager.mark_user_activity()
        else:
            print("[ListeningState] No STT engine configured.")

        # 🔥 CRITICAL FIX — Save transcript to the manager
        manager.last_user_text = transcript

        # Move to Processing
        return manager.processing_state
