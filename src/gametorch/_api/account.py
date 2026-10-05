"""Account and health endpoints."""

from __future__ import annotations

from .._rate_limit import Concurrency, RateClass
from .._types import OkResponse


class AccountMixin:
    """Account and health endpoints."""

    async def ensure_user(self) -> OkResponse:
        """Ensures a mirrored user row exists for the caller.

        ``POST /users/me``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "POST",
            "users/me",
            rate_class=RateClass.WRITES,
            route="POST /users/me",
            concurrency=Concurrency.NONE,
        )

    async def health(self) -> str:
        """Returns the API health status (``"ok"`` when healthy).

        ``GET /health``
        """
        download = await self._send_download(  # type: ignore[attr-defined]
            "GET",
            "health",
            rate_class=RateClass.UNLIMITED,
            route="GET /health",
            concurrency=Concurrency.NONE,
        )
        return download.data.decode("utf-8", errors="replace").strip()


__all__ = ["AccountMixin"]
