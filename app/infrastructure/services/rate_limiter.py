import time
from collections import deque
from typing import Deque, Dict

class InMemoryRateLimiter:
    """
    Simple fixed-window limiter per key. For prod, replace with Redis-based impl.
    """
    def __init__(self):
        self._buckets: Dict[str, Deque[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        dq = self._buckets.setdefault(key, deque())
        # drop old
        while dq and (now - dq[0] > window_seconds):
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True

rate_limiter = InMemoryRateLimiter()
