from abc import ABC, abstractmethod
from typing import Optional

class State(ABC):
    """Base interface class for all Baymax states."""

    @abstractmethod
    def on_enter(self) -> None:
        """Called when the state becomes active."""
        pass

    @abstractmethod
    def on_exit(self) -> None:
        """Called when the state is deactivated."""
        pass

    @abstractmethod
    def handle(self, manager, user_input: Optional[str]):
        """
        Process one cycle of logic for this state.
        Return the next state object, or None to stay in the same state.
        """
        pass
