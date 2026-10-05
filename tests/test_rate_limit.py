"""Tests for the client-side rate limiter."""

from __future__ import annotations

import time

from gametorch._rate_limit import Concurrency, RateClass, RateLimiter, _Bucket


def test_bucket_allows_burst_then_throttles() -> None:
    bucket = _Bucket(2.0, 1.0)
    now = time.monotonic()
    assert bucket.poll(now) is None
    assert bucket.poll(now) is None
    wait = bucket.poll(now)
    assert wait is not None
    assert wait >= 0.9


def test_writes_bucket_has_large_burst() -> None:
    bucket = _Bucket(100.0, 5.0)
    now = time.monotonic()
    for _ in range(100):
        assert bucket.poll(now) is None
    assert bucket.poll(now) is not None


def test_bucket_refills_over_time() -> None:
    bucket = _Bucket(1.0, 10.0)
    now = time.monotonic()
    assert bucket.poll(now) is None
    assert bucket.poll(now) is not None
    # A refill period restores exactly one token.
    assert bucket.poll(now + 0.11) is None


async def test_disabled_limiter_never_blocks() -> None:
    limiter = RateLimiter(False)
    for _ in range(1000):
        await limiter.acquire(RateClass.TIER1, "route")
    async with limiter.concurrency(Concurrency.FRAME_GENERATION):
        pass


async def test_enabled_limiter_throttles_second_request() -> None:
    limiter = RateLimiter(True)
    await limiter.acquire(RateClass.TIER1, "GET /x")
    started = time.monotonic()
    await limiter.acquire(RateClass.TIER1, "GET /x")
    assert time.monotonic() - started >= 0.5


async def test_unlimited_class_is_not_throttled() -> None:
    limiter = RateLimiter(True)
    for _ in range(50):
        await limiter.acquire(RateClass.UNLIMITED, "GET /health")
