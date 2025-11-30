from interfaces.state_interface import State
from tts.elevenlabs_tts import ElevenLabsTTS

class SpeakingState(State):

    def __init__(self):
        self._tts = None

    def _ensure_tts(self):
        if self._tts:
            return self._tts

        try:
            self._tts = ElevenLabsTTS()
        except Exception as exc:
            print("[SpeakingState] TTS init error:", exc)
            self._tts = None

        return self._tts

    def on_enter(self):
        print("[State] Entering SpeakingState")

    def on_exit(self):
        print("[State] Exiting SpeakingState")

    def handle(self, manager, user_input):
        print("[SpeakingState] Handling:", user_input)

        tts = self._ensure_tts()
        if not tts:
            print("[SpeakingState] No TTS engine available.")
            return manager.idle_state

        try:
            tts.speak("Hello, I am Baymax.")
        except Exception as e:
            print("[SpeakingState] TTS Error:", e)

        # After speaking, go to idle
        return manager.idle_state
