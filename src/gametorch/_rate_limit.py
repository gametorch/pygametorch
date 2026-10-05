"""Client-side rate limiting that mirrors GameTorch's published limits.

GameTorch rate limits every account per route and returns ``429`` when a limit
is exceeded. To be a good citizen by default, the SDK throttles requests locally
before they are sent:

* **Tier 1** — 1 request/second per route: generation creates, frame generation
  and animation exports.
* **Tier 2** — 2 requests/second per route: content, usage, search and
  single-item reads.
* **Writes** — one shared token bucket (100-request burst, 5 requests/second
  refill) for creation, archive/unarchive and metadata writes.
* **Concurrency** — at most 25 in-flight hold-creating requests and 5 concurrent
  frame generations.

The limiter is enabled by default and can be disabled with ``rate_limit=False``.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

__all__ = ["Concurrency", "RateClass", "RateLimiter"]

# The per-account concurrency caps published by GameTorch.
MAX_OUTSTANDING_HOLDS = 25
# Maximum concurrent animation-frame generations per account.
MAX_FRAME_GENERATIONS = 5


class RateClass(Enum):
    """The rate-limit bucket an operation belongs to."""

    TIER1 = "tier1"
    TIER2 = "tier2"
    WRITES = "writes"
    UNLIMITED = "unlimited"


@dataclass(frozen=True)
class Concurrency:
    """Concurrency caps that apply to an operation."""

    hold: bool = False
    frame_generation: bool = False


Concurrency.NONE = Concurrency()  # type: ignore[attr-defined]
Concurrency.HOLD = Concurrency(hold=True)  # type: ignore[attr-defined]
Concurrency.FRAME_GENERATION = Concurrency(hold=True, frame_generation=True)  # type: ignore[attr-defined]


class _Bucket:
    """A token bucket. ``poll`` consumes a token or returns the seconds to wait."""

    __slots__ = ("capacity", "last", "refill_per_sec", "tokens")

    def __init__(self, capacity: float, refill_per_sec: float) -> None:
        self.tokens = capacity
        self.last = time.monotonic()
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.last)
        if elapsed > 0.0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
            self.last = now

    def poll(self, now: float) -> float | None:
        self._refill(now)
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return None
        deficit = 1.0 - self.tokens
        return deficit / self.refill_per_sec


class RateLimiter:
    """The SDK's shared rate limiter."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled
        self._per_route: dict[str, _Bucket] = {}
        self._writes = _Bucket(100.0, 5.0)
        self._holds = asyncio.Semaphore(MAX_OUTSTANDING_HOLDS)
        self._frames = asyncio.Semaphore(MAX_FRAME_GENERATIONS)

    @staticmethod
    def _bucket_params(rate_class: RateClass) -> tuple[float, float]:
        match rate_class:
            case RateClass.TIER1:
                return (1.0, 1.0)
            case RateClass.TIER2:
                return (1.0, 2.0)
            case RateClass.WRITES:
                return (100.0, 5.0)
            case RateClass.UNLIMITED:
                return (float("inf"), float("inf"))
        raise ValueError(f"unknown rate class: {rate_class!r}")

    async def acquire(self, rate_class: RateClass, route: str) -> None:
        """Waits until the operation's rate bucket allows another request."""
        if not self._enabled or rate_class is RateClass.UNLIMITED:
            return

        while True:
            now = time.monotonic()
            if rate_class is RateClass.WRITES:
                wait = self._writes.poll(now)
            else:
                capacity, refill = self._bucket_params(rate_class)
                bucket = self._per_route.get(route)
                if bucket is None:
                    bucket = _Bucket(capacity, refill)
                    self._per_route[route] = bucket
                wait = bucket.poll(now)

            if wait is None:
                return
            await asyncio.sleep(wait)

    @asynccontextmanager
    async def concurrency(self, concurrency: Concurrency) -> AsyncIterator[None]:
        """Acquires the concurrency permits required by an operation."""
        if not self._enabled:
            yield
            return

        acquired: list[asyncio.Semaphore] = []
        try:
            if concurrency.hold:
                await self._holds.acquire()
                acquired.append(self._holds)
            if concurrency.frame_generation:
                await self._frames.acquire()
                acquired.append(self._frames)
            yield
        finally:
            for semaphore in reversed(acquired):
                semaphore.release()
