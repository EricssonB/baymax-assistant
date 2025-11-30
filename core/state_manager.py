"""Legacy shim to avoid duplicate StateManager implementations.

The authoritative StateManager now lives in states/state_manager.py.
This module simply re-exports that implementation for backward compatibility.
"""

from states.state_manager import StateManager  # noqa: F401

__all__ = ["StateManager"]
