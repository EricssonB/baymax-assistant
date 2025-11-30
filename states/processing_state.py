from interfaces.state_interface import State

class ProcessingState(State):
    def on_enter(self):
        print("[State] Entering ProcessingState")

    def on_exit(self):
        print("[State] Exiting ProcessingState")

    def handle(self, manager, user_input):
        text = getattr(manager, "last_user_text", None) or user_input
        print("[ProcessingState] Handling:", text)

        # Placeholder for LLM hook would go here; clear consumed text
        manager.last_user_text = None

        # After processing, move to speaking state
        return manager.speaking_state
