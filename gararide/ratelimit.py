"""Tiny in-process rate limiter (sliding window) to blunt spam and protect the
server. Good enough for the single-process pilot; resets on restart. Limits are
deliberately generous — they stop flooding, not normal use.
"""
from __future__ import annotations

import threading
import time

_hits: dict[str, list[float]] = {}
_lock = threading.Lock()


def allow(key: str, max_calls: int, window_s: float) -> bool:
    """True if this key may act now; records the hit. False once the window is full."""
    now = time.monotonic()
    cutoff = now - window_s
    with _lock:
        q = _hits.setdefault(key, [])
        while q and q[0] < cutoff:
            q.pop(0)
        if len(q) >= max_calls:
            return False
        q.append(now)
        return True
