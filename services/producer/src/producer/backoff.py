"""Exponential backoff with jitter for stream reconnects."""

import random


class ExponentialBackoff:
    """Delays grow as base * 2^attempt up to a cap, with +/- `jitter` relative noise."""

    def __init__(self, base: float = 1.0, cap: float = 60.0, jitter: float = 0.2) -> None:
        self._base = base
        self._cap = cap
        self._jitter = jitter
        self._attempt = 0

    def next_delay(self) -> float:
        delay = min(self._base * (2**self._attempt), self._cap)
        self._attempt += 1
        noise = delay * self._jitter
        return max(0.0, delay + random.uniform(-noise, noise))

    def reset(self) -> None:
        self._attempt = 0
