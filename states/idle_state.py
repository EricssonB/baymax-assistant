from interfaces.state_interface import State

class IdleState(State):
    def on_enter(self):
        print("[State] Entering IdleState")

    def on_exit(self):
        print("[State] Exiting IdleState")

    def handle(self, manager, user_input):
        print("[IdleState] Handling:", user_input)

        # In demo mode, always return to sleep between cycles
        return manager.sleep_state
