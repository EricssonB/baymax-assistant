from interfaces.state_interface import State

class ListeningState(State):
    def on_enter(self):
        print("[State] Entering ListeningState")

    def on_exit(self):
        print("[State] Exiting ListeningState")

    def handle(self, manager, user_input):
        print("[ListeningState] Handling:", user_input)

        # If we have some user speech, move to processing
        if user_input not in (None, "hey baymax"):
            return manager.processing_state

        return None
