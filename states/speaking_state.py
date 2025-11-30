from interfaces.state_interface import State

class SpeakingState(State):
    def on_enter(self):
        print("[State] Entering SpeakingState")

    def on_exit(self):
        print("[State] Exiting SpeakingState")

    def handle(self, manager, user_input):
        print("[SpeakingState] Handling:", user_input)

        # After speaking, go to idle
        return manager.idle_state
