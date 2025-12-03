from interfaces.state_interface import State

class IdleState(State):
    def on_enter(self):
        print("[State] >>> IdleState")

    def on_exit(self):
        print("[State] <<< IdleState")

    def handle(self, manager, user_input):
        if user_input is not None:
            print("[IdleState] Handling:", user_input)

        # Hand control back to ListeningState so Baymax keeps the loop alive
        return manager.listening_state
