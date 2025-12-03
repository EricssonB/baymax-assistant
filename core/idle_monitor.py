"""Background idle monitor for Baymax 2.0."""

from __future__ import annotations

import threading
import time
from typing import Optional


class IdleMonitor:
    """Monitors user inactivity and nudges Baymax to sleep when idle."""

    def __init__(
        self,
        manager,
        *,
        warn_after: float = 45.0,
        sleep_after: float = 60.0,
        poll_interval: float = 1.0,
    ) -> None:
        self._manager = manager
        self._warn_after = warn_after
        self._sleep_after = max(sleep_after, warn_after)
        self._poll_interval = max(poll_interval, 0.5)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_warning_ts = 0.0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="BaymaxIdleMonitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._last_warning_ts = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self._poll_interval)

            if not self._manager.streaming_enabled:
                continue

            if not self._manager.is_awake:
                self._last_warning_ts = 0.0
                continue

            if self._manager.is_speaking:
                continue

            idle_seconds = time.time() - self._manager.last_user_activity

            if idle_seconds >= self._sleep_after:
                self._last_warning_ts = 0.0
                self._manager.queue_idle_sleep_message()
                continue

            if idle_seconds >= self._warn_after:
                now = time.time()
                if now - self._last_warning_ts >= 10.0:
                    self._manager.queue_idle_prompt()
                    self._last_warning_ts = now