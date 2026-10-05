"""Saved animation endpoints."""

from __future__ import annotations

from uuid import UUID

from .._errors import ConfigError
from .._rate_limit import Concurrency, RateClass
from .._types import (
    ArchiveResponse,
    AssetMetadataResponse,
    AssetNameResponse,
    ListParams,
    Page,
    Paginator,
)
from ..models import SavedAnimation, SavedAnimationsResponse
from . import list_query

IdLike = UUID | str


class SaveAnimationBuilder:
    """Builder for creating a saved animation."""

    def __init__(self, client, dispatch, project_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._generation_id: IdLike | None = None
        self._start_frame: int | None = None
        self._end_frame: int | None = None
        self._name: str | None = None

    def generation_id(self, generation_id: IdLike) -> SaveAnimationBuilder:
        """Sets the source animation run id (required)."""
        self._generation_id = generation_id
        return self

    def range(self, start_frame: int, end_frame: int) -> SaveAnimationBuilder:
        """Sets the inclusive frame range (required)."""
        self._start_frame = start_frame
        self._end_frame = end_frame
        return self

    def name(self, name: str) -> SaveAnimationBuilder:
        """Sets an optional name for the saved animation."""
        self._name = name
        return self

    def send(self) -> SavedAnimation:
        """Creates the saved animation."""
        return self._dispatch(self._send())

    async def _send(self) -> SavedAnimation:
        if self._generation_id is None:
            raise ConfigError("saved animation requires a generation_id")
        if self._start_frame is None:
            raise ConfigError("saved animation requires a start_frame")
        if self._end_frame is None:
            raise ConfigError("saved animation requires an end_frame")
        body: dict[str, object] = {
            "generation_id": str(self._generation_id),
            "start_frame": self._start_frame,
            "end_frame": self._end_frame,
        }
        if self._name is not None:
            body["name"] = self._name
        return await self._client._send_json(
            SavedAnimation,
            "POST",
            f"projects/{self._project_id}/saved-animations",
            rate_class=RateClass.WRITES,
            route="POST /projects/{project_id}/saved-animations",
            concurrency=Concurrency.NONE,
            json_body=body,
        )


class SavedAnimationsMixin:
    """Saved animation endpoints."""

    async def list_saved_animations(
        self, project_id: IdLike, params: ListParams | None = None
    ) -> SavedAnimationsResponse:
        """Lists a project's saved animations.

        ``GET /projects/{project_id}/saved-animations``
        """
        query = list_query(params or ListParams())
        return await self._send_json(  # type: ignore[attr-defined]
            SavedAnimationsResponse,
            "GET",
            f"projects/{project_id}/saved-animations",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/saved-animations",
            concurrency=Concurrency.NONE,
            params=query,
        )

    def save_animation(self, project_id: IdLike) -> SaveAnimationBuilder:
        """Starts building a saved animation from a range of an animation run.

        ``POST /projects/{project_id}/saved-animations``
        """
        return SaveAnimationBuilder(self, self._dispatch, project_id)  # type: ignore[attr-defined]

    async def get_saved_animation(self, saved_id: IdLike) -> SavedAnimation:
        """Returns one saved animation.

        ``GET /saved-animations/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            SavedAnimation,
            "GET",
            f"saved-animations/{saved_id}",
            rate_class=RateClass.TIER2,
            route="GET /saved-animations/{id}",
            concurrency=Concurrency.NONE,
        )

    async def rename_saved_animation(self, saved_id: IdLike, name: str | None) -> AssetNameResponse:
        """Renames a saved animation. Pass ``None`` to clear the name.

        ``PATCH /saved-animations/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetNameResponse,
            "PATCH",
            f"saved-animations/{saved_id}",
            rate_class=RateClass.WRITES,
            route="PATCH /saved-animations/{id}",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def put_saved_animation_metadata(
        self, saved_id: IdLike, metadata: dict[str, str]
    ) -> AssetMetadataResponse:
        """Replaces a saved animation's metadata.

        ``PUT /saved-animations/{id}/metadata``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetMetadataResponse,
            "PUT",
            f"saved-animations/{saved_id}/metadata",
            rate_class=RateClass.WRITES,
            route="PUT /saved-animations/{id}/metadata",
            concurrency=Concurrency.NONE,
            json_body={"metadata": metadata},
        )

    async def archive_saved_animation(self, saved_id: IdLike) -> ArchiveResponse:
        """Archives a saved animation.

        ``POST /saved-animations/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"saved-animations/{saved_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /saved-animations/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_saved_animation(self, saved_id: IdLike) -> ArchiveResponse:
        """Restores an archived saved animation.

        ``POST /saved-animations/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"saved-animations/{saved_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /saved-animations/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    async def delete_saved_animation(self, saved_id: IdLike) -> None:
        """Permanently deletes a saved animation.

        ``DELETE /saved-animations/{id}``
        """
        await self._send_ok(  # type: ignore[attr-defined]
            "DELETE",
            f"saved-animations/{saved_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /saved-animations/{id}",
            concurrency=Concurrency.NONE,
        )

    def stream_saved_animations(
        self, project_id: IdLike, include_archived: bool = False
    ) -> Paginator[SavedAnimation]:
        """Streams a project's saved animations page by page."""

        async def fetch(cursor: str | None) -> Page[SavedAnimation]:
            params = ListParams(before=cursor, include_archived=include_archived)
            response = await self.list_saved_animations(project_id, params)
            return Page(
                items=response.saved_animations,
                next_cursor=response.next_cursor,
                total=response.total,
            )

        return Paginator(fetch, self._dispatch)  # type: ignore[attr-defined]


__all__ = ["SaveAnimationBuilder", "SavedAnimationsMixin"]
