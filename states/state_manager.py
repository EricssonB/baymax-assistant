from interfaces.state_interface import State
from states.sleep_state import SleepState
from states.wake_state import WakeState
from states.listening_state import ListeningState
from states.processing_state import ProcessingState
from states.speaking_state import SpeakingState
from states.idle_state import IdleState

class StateManager:
    """Holds and transitions between all Baymax states."""

    def __init__(self):
        # Instantiate all states
        self.sleep_state = SleepState()
        self.wake_state = WakeState()
        self.listening_state = ListeningState()
        self.processing_state = ProcessingState()
        self.speaking_state = SpeakingState()
        self.idle_state = IdleState()

        # Start in sleep state
        self.current_state: State = self.sleep_state
        self.last_user_text = None

        enter_hook = getattr(self.current_state, "on_enter", None)
        if enter_hook:
            enter_hook()

    def set_state(self, new_state: State) -> None:
        if not new_state or new_state is self.current_state:
            return

        if self.current_state:
            exit_hook = getattr(self.current_state, "on_exit", None)
            if exit_hook:
                exit_hook()

        self.current_state = new_state

        enter_hook = getattr(self.current_state, "on_enter", None)
        if enter_hook:
            enter_hook()

    def update(self, user_input=None):
        """Runs one cycle of the current state logic."""
        next_state = self.current_state.handle(self, user_input)
        if next_state and next_state != self.current_state:
            self.set_state(next_state)
