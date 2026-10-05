"""Art style endpoints."""

from __future__ import annotations

from uuid import UUID

from .._rate_limit import Concurrency, RateClass
from .._types import OkResponse
from ..models import ArtStyle, ArtStylesResponse, ArtStyleSuggestion

IdLike = UUID | str


class ArtStylesMixin:
    """Art style endpoints."""

    async def list_art_styles(self, project_id: IdLike) -> ArtStylesResponse:
        """Lists a project's reusable art styles.

        ``GET /projects/{project_id}/art-styles``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArtStylesResponse,
            "GET",
            f"projects/{project_id}/art-styles",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/art-styles",
            concurrency=Concurrency.NONE,
        )

    async def create_art_style(self, project_id: IdLike, name: str) -> ArtStyle:
        """Creates an art style.

        ``POST /projects/{project_id}/art-styles``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArtStyle,
            "POST",
            f"projects/{project_id}/art-styles",
            rate_class=RateClass.WRITES,
            route="POST /projects/{project_id}/art-styles",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def generate_art_style(self, project_id: IdLike) -> ArtStyleSuggestion:
        """Returns a fresh suggested art style for the user to review.

        ``POST /projects/{project_id}/art-styles/generate``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArtStyleSuggestion,
            "POST",
            f"projects/{project_id}/art-styles/generate",
            rate_class=RateClass.TIER2,
            route="POST /projects/{project_id}/art-styles/generate",
            concurrency=Concurrency.NONE,
        )

    async def delete_art_style(self, art_style_id: IdLike) -> OkResponse:
        """Deletes an art style.

        ``DELETE /art-styles/{art_style_id}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"art-styles/{art_style_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /art-styles/{art_style_id}",
            concurrency=Concurrency.NONE,
        )


__all__ = ["ArtStylesMixin"]
