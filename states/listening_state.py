from interfaces.state_interface import State
import time
from audio.microphone import Microphone
from stt.deepgram_stt import DeepgramSTT

class ListeningState(State):
    def __init__(self):
        self.mic = Microphone()
        self.stt = DeepgramSTT()

    def on_enter(self):
        print("[State] Entering ListeningState")
        time.sleep(0.2)

    def on_exit(self):
        print("[State] Exiting ListeningState")

    def handle(self, manager, user_input):
        print("[ListeningState] Recording speech...")

        # Record audio to file
        input_file = "audio/input.wav"
        try:
            self.mic.record_to_file(input_file, duration=3)
        except Exception as e:
            print("[ListeningState] Mic error:", e)
            return manager.idle_state

        # Transcribe audio
        print("[ListeningState] Transcribing...")
        text = self.stt.transcribe(input_file)

        print("[ListeningState] Transcript:", text)

        cleaned = text.strip() if text else ""
        manager.last_user_text = cleaned or None

        if cleaned:
            return manager.processing_state

        # If no valid text, stay here or go idle?
        return manager.idle_state
