import time
from collections import deque
from typing import Callable


class RateLimiter:
    """Allows at most ``limit`` actions within any ``window_seconds`` (a sliding window).

    One instance guards one thing for one connection, so it needs no keys and goes away
    together with the connection.
    """

    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._recent: deque[float] = deque()  # times of the actions within the current window

    def try_acquire(self) -> float | None:
        """Count one action if allowed and return None; otherwise return the seconds to wait.

        Rejected attempts are not counted, so someone who keeps trying is let through
        as soon as the window has room again.
        """
        now = self._clock()
        while self._recent and self._recent[0] <= now - self.window_seconds:
            self._recent.popleft()

        if len(self._recent) >= self.limit:
            return self._recent[0] + self.window_seconds - now

        self._recent.append(now)
        return None
