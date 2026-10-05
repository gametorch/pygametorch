"""Sound generation and sound asset endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from .._errors import ConfigError
from .._rate_limit import Concurrency, RateClass
from .._types import (
    ArchiveResponse,
    AssetMetadataResponse,
    AssetNameResponse,
    Download,
    JobCreated,
    ListParams,
    Page,
    Paginator,
)
from ..models import SoundGeneration, SoundGenerationsResponse
from . import list_query

IdLike = UUID | str


class SoundGenerationBuilder:
    """Builder for a sound generation.

    Created by :meth:`~gametorch.AsyncClient.generate_sound`. ``prompt`` and
    ``sound_model`` are required.
    """

    def __init__(self, client, dispatch, project_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._prompt: str | None = None
        self._sound_model: str | None = None
        self._response_format: str | None = None
        self._request_id: IdLike | None = None

    def prompt(self, prompt: str) -> SoundGenerationBuilder:
        """Sets the generation prompt (required)."""
        self._prompt = prompt
        return self

    def sound_model(self, sound_model: str) -> SoundGenerationBuilder:
        """Sets the sound model id (required). See ``sound_models()``."""
        self._sound_model = sound_model
        return self

    def response_format(self, response_format: str) -> SoundGenerationBuilder:
        """Sets the output format, for example ``mp3`` or ``pcm``."""
        self._response_format = response_format
        return self

    def request_id(self, request_id: IdLike) -> SoundGenerationBuilder:
        """Overrides the idempotency key (defaults to a fresh UUID v4)."""
        self._request_id = request_id
        return self

    def send(self) -> JobCreated:
        """Sends the sound generation request."""
        return self._dispatch(self._send())

    async def _send(self) -> JobCreated:
        if self._prompt is None:
            raise ConfigError("sound generation requires a prompt")
        if self._sound_model is None:
            raise ConfigError("sound generation requires a sound_model")

        body = {
            "request_id": str(self._request_id or uuid4()),
            "prompt": self._prompt,
            "sound_model": self._sound_model,
        }
        if self._response_format is not None:
            body["response_format"] = self._response_format

        return await self._client._send_json(
            JobCreated,
            "POST",
            f"projects/{self._project_id}/sound-generations",
            rate_class=RateClass.TIER1,
            route="POST /projects/{project_id}/sound-generations",
            concurrency=Concurrency.HOLD,
            json_body=body,
        )


class SoundsMixin:
    """Sound generation and sound asset endpoints."""

    def generate_sound(self, project_id: IdLike) -> SoundGenerationBuilder:
        """Starts building a sound generation."""
        return SoundGenerationBuilder(self, self._dispatch, project_id)  # type: ignore[attr-defined]

    async def list_sound_generations(
        self, project_id: IdLike, params: ListParams | None = None
    ) -> SoundGenerationsResponse:
        """Lists a project's sound generations.

        ``GET /projects/{project_id}/sound-generations``
        """
        query = list_query(params or ListParams())
        return await self._send_json(  # type: ignore[attr-defined]
            SoundGenerationsResponse,
            "GET",
            f"projects/{project_id}/sound-generations",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/sound-generations",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def get_sound_generation(
        self, generation_id: IdLike, include_archived: bool = False
    ) -> SoundGeneration:
        """Returns one sound generation and its assets.

        ``GET /sound-generations/{id}``
        """
        query = [("include_archived", "true")] if include_archived else None
        return await self._send_json(  # type: ignore[attr-defined]
            SoundGeneration,
            "GET",
            f"sound-generations/{generation_id}",
            rate_class=RateClass.TIER2,
            route="GET /sound-generations/{id}",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def sound_asset_content(self, asset_id: IdLike) -> Download:
        """Returns the audio bytes of a sound asset.

        ``GET /sound-assets/{id}/content``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"sound-assets/{asset_id}/content",
            rate_class=RateClass.TIER2,
            route="GET /sound-assets/{id}/content",
            concurrency=Concurrency.NONE,
        )

    async def rename_sound_asset(self, asset_id: IdLike, name: str | None) -> AssetNameResponse:
        """Renames a sound asset. Pass ``None`` to clear the name.

        ``PATCH /sound-assets/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetNameResponse,
            "PATCH",
            f"sound-assets/{asset_id}",
            rate_class=RateClass.WRITES,
            route="PATCH /sound-assets/{id}",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def put_sound_asset_metadata(
        self, asset_id: IdLike, metadata: dict[str, str]
    ) -> AssetMetadataResponse:
        """Replaces a sound asset's metadata.

        ``PUT /sound-assets/{id}/metadata``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetMetadataResponse,
            "PUT",
            f"sound-assets/{asset_id}/metadata",
            rate_class=RateClass.WRITES,
            route="PUT /sound-assets/{id}/metadata",
            concurrency=Concurrency.NONE,
            json_body={"metadata": metadata},
        )

    async def archive_sound_asset(self, asset_id: IdLike) -> ArchiveResponse:
        """Archives a sound asset.

        ``POST /sound-assets/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"sound-assets/{asset_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /sound-assets/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_sound_asset(self, asset_id: IdLike) -> ArchiveResponse:
        """Restores an archived sound asset.

        ``POST /sound-assets/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"sound-assets/{asset_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /sound-assets/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    async def delete_sound_asset(self, asset_id: IdLike) -> None:
        """Permanently deletes a sound asset.

        ``DELETE /sound-assets/{id}``
        """
        await self._send_ok(  # type: ignore[attr-defined]
            "DELETE",
            f"sound-assets/{asset_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /sound-assets/{id}",
            concurrency=Concurrency.NONE,
        )

    async def archive_sound_generation(self, generation_id: IdLike) -> ArchiveResponse:
        """Archives a whole sound generation.

        ``POST /sound-generations/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"sound-generations/{generation_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /sound-generations/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_sound_generation(self, generation_id: IdLike) -> ArchiveResponse:
        """Restores an archived sound generation.

        ``POST /sound-generations/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"sound-generations/{generation_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /sound-generations/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    def stream_sound_generations(
        self, project_id: IdLike, include_archived: bool = False
    ) -> Paginator[SoundGeneration]:
        """Streams a project's sound generations page by page."""

        async def fetch(cursor: str | None) -> Page[SoundGeneration]:
            params = ListParams(before=cursor, include_archived=include_archived)
            response = await self.list_sound_generations(project_id, params)
            return Page(
                items=response.sound_generations,
                next_cursor=response.next_cursor,
                total=response.total,
            )

        return Paginator(fetch, self._dispatch)  # type: ignore[attr-defined]


__all__ = ["SoundGenerationBuilder", "SoundsMixin"]
