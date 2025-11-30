from interfaces.state_interface import State

class ProcessingState(State):
    def on_enter(self):
        print("[State] Entering ProcessingState")

    def on_exit(self):
        print("[State] Exiting ProcessingState")

    def handle(self, manager, user_input):
        print("[ProcessingState] Handling:", user_input)

        # After processing, move to speaking state
        return manager.speaking_state
