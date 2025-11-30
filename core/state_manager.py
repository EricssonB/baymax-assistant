from typing import Dict, Optional
from interfaces.state_interface import StateInterface

class StateManager:
    """Handles transitions and execution of Baymax states."""

    def __init__(self):
        self.states: Dict[str, StateInterface] = {}
        self.current_state: Optional[StateInterface] = None

    def add_state(self, name: str, state: StateInterface) -> None:
        """Register a new state in the manager."""
        self.states[name] = state

    def set_state(self, name: str) -> None:
        """Transition to a new state by name."""
        if self.current_state:
            self.current_state.on_exit()

        self.current_state = self.states.get(name)

        if self.current_state:
            self.current_state.on_enter()

    def handle_input(self, text: Optional[str]) -> None:
        """Forward input to the active state and process transitions."""
        if not self.current_state:
            return

        next_state = self.current_state.handle_input(text)

        if next_state and next_state in self.states:
            self.set_state(next_state)
