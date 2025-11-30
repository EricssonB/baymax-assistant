from interfaces.state_interface import State

class WakeState(State):
    def on_enter(self):
        print("[State] Entering WakeState")

    def on_exit(self):
        print("[State] Exiting WakeState")

    def handle(self, manager, user_input):
        print("[WakeState] Handling:", user_input)

        # After wake confirmation, move to listening state
        return manager.listening_state
