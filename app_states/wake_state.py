from interfaces.state_interface import State

WELCOME_LINE = "Hello, I am Baymax, your personal healthcare companion."

class WakeState(State):
    def on_enter(self):
        print("[State] >>> WakeState")

    def on_exit(self):
        print("[State] <<< WakeState")

    def handle(self, manager, user_input):
        print("[WakeState] Handling:", user_input)

        if not getattr(manager, "last_bot_text", None):
            if hasattr(manager, "clear_transcripts"):
                manager.clear_transcripts()
            manager.last_bot_text = WELCOME_LINE
            manager.set_post_speech_state(manager.listening_state)
            return manager.speaking_state

        # After wake confirmation, move to listening state
        return manager.listening_state
