from .base_state import State

class SleepState(State):
    """Baymax is asleep and waiting for the wake word."""

    def handle(self, manager, user_input=None):
        print("[State] SleepState")

        # Placeholder wake-word logic
        if user_input and user_input.lower() == "hey baymax":
            print("[SleepState] Wake word detected!")
            return manager.wake_state

        # Stay in sleep
        return self

