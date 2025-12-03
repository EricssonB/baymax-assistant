"""Event primitives shared across Baymax subsystems."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class WakeEventType(Enum):
    """High-level wake-cycle events emitted by streaming services."""

    WAKE = auto()
    SLEEP = auto()
    SATISFIED = auto()


@dataclass(frozen=True)
class WakeEvent:
    """Represents a wake-cycle change detected in audio."""

    event_type: WakeEventType
    transcript: str


@dataclass(frozen=True)
class TranscriptEvent:
    """Represents a piece of speech recognized by STT."""

    text: str
    is_final: bool
    should_process: bool
    raw: Optional[object] = None