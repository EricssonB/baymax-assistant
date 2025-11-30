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

    def set_state(self, new_state: State) -> None:
        self.current_state = new_state

    def update(self, user_input=None):
        """Runs one cycle of the current state logic."""
        next_state = self.current_state.handle(self, user_input)
        if next_state and next_state != self.current_state:
            self.set_state(next_state)
