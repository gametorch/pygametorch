"""Usage and spending endpoints."""

from __future__ import annotations

from .._rate_limit import Concurrency, RateClass
from .._types import Page, Paginator
from ..models import Usage, UsageHistogram, UsageRecord


class UsageMixin:
    """Usage and spending endpoints."""

    async def usage(self, before: str | None = None, split: str | None = None) -> Usage:
        """Returns the credit balance, per-source summary and operation log.

        ``GET /usage``
        """
        query: list[tuple[str, str]] = []
        if before is not None:
            query.append(("before", before))
        if split is not None:
            query.append(("split", split))
        return await self._send_json(  # type: ignore[attr-defined]
            Usage,
            "GET",
            "usage",
            rate_class=RateClass.TIER2,
            route="GET /usage",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def usage_histogram(
        self,
        range: str | None = None,
        source: str | None = None,
        split: str | None = None,
    ) -> UsageHistogram:
        """Returns dense time buckets of spend split by source.

        ``GET /usage/histogram``
        """
        query: list[tuple[str, str]] = []
        if range is not None:
            query.append(("range", range))
        if source is not None:
            query.append(("source", source))
        if split is not None:
            query.append(("split", split))
        return await self._send_json(  # type: ignore[attr-defined]
            UsageHistogram,
            "GET",
            "usage/histogram",
            rate_class=RateClass.TIER2,
            route="GET /usage/histogram",
            concurrency=Concurrency.NONE,
            params=query,
        )

    def stream_usage(self, split: str | None = None) -> Paginator[UsageRecord]:
        """Streams the operation log page by page."""

        async def fetch(cursor: str | None) -> Page[UsageRecord]:
            response = await self.usage(cursor, split)
            return Page(
                items=response.records,
                next_cursor=response.next_cursor,
                total=response.total,
            )

        return Paginator(fetch, self._dispatch)  # type: ignore[attr-defined]


__all__ = ["UsageMixin"]
