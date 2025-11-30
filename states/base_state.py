class State:
    """Base class for all states in Baymax."""
    
    def handle(self, manager, user_input=None):
        """
        Each state must implement its own handle() method.
        """
        raise NotImplementedError("States must implement handle().")
