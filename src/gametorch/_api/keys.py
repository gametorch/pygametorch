"""API key management endpoints."""

from __future__ import annotations

from uuid import UUID

from .._rate_limit import Concurrency, RateClass
from .._types import OkResponse
from ..models import (
    ApiKey,
    ApiKeyWithSecret,
    CreateApiKeyRequest,
    KeysResponse,
    UpdateApiKeyRequest,
)


class KeysMixin:
    """API key management endpoints (admin keys only)."""

    async def list_keys(self) -> KeysResponse:
        """Lists the API keys in the caller's scope. Admin-only for organizations.

        ``GET /keys``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            KeysResponse,
            "GET",
            "keys",
            rate_class=RateClass.TIER2,
            route="GET /keys",
            concurrency=Concurrency.NONE,
        )

    async def create_key(self, request: CreateApiKeyRequest) -> ApiKeyWithSecret:
        """Creates an API key. The full key is returned exactly once.

        ``POST /keys``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ApiKeyWithSecret,
            "POST",
            "keys",
            rate_class=RateClass.WRITES,
            route="POST /keys",
            concurrency=Concurrency.NONE,
            json_body=request.to_body(),
        )

    async def update_key(self, key_id: UUID, request: UpdateApiKeyRequest) -> ApiKey:
        """Updates an API key. Only the fields set on ``request`` are changed.

        ``PATCH /keys/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ApiKey,
            "PATCH",
            f"keys/{key_id}",
            rate_class=RateClass.WRITES,
            route="PATCH /keys/{id}",
            concurrency=Concurrency.NONE,
            json_body=request.to_body(),
        )

    async def delete_key(self, key_id: UUID) -> OkResponse:
        """Revokes an API key.

        ``DELETE /keys/{id}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"keys/{key_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /keys/{id}",
            concurrency=Concurrency.NONE,
        )


__all__ = ["KeysMixin"]
