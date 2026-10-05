"""Sprite generation and sprite asset endpoints."""

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
    SpriteMode,
)
from ..models import Asset, Generation, GenerationsResponse, SpriteAssetsResponse
from . import list_query

IdLike = UUID | str


class SpriteGenerationBuilder:
    """Builder for a sprite generation.

    Created by :meth:`~gametorch.AsyncClient.generate_sprite`. ``prompt`` and
    ``image_model`` are required; everything else has a sensible default.
    """

    def __init__(self, client, dispatch, project_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._prompt: str | None = None
        self._mode: SpriteMode = SpriteMode.SINGLE
        self._image_model: str | None = None
        self._text_model: str | None = None
        self._quality: str | None = None
        self._resolution: str | None = None
        self._base_asset_id: IdLike | None = None
        self._request_id: IdLike | None = None

    def prompt(self, prompt: str) -> SpriteGenerationBuilder:
        """Sets the generation prompt (required)."""
        self._prompt = prompt
        return self

    def mode(self, mode: SpriteMode) -> SpriteGenerationBuilder:
        """Sets the generation mode. Defaults to :attr:`SpriteMode.SINGLE`."""
        self._mode = mode
        return self

    def image_model(self, image_model: str) -> SpriteGenerationBuilder:
        """Sets the image model id (required). See ``sprite_models()``."""
        self._image_model = image_model
        return self

    def text_model(self, text_model: str) -> SpriteGenerationBuilder:
        """Sets the prompt-enhancement text model. Use ``"none"`` to disable."""
        self._text_model = text_model
        return self

    def no_text_model(self) -> SpriteGenerationBuilder:
        """Disables prompt enhancement."""
        self._text_model = "none"
        return self

    def quality(self, quality: str) -> SpriteGenerationBuilder:
        """Sets the quality setting."""
        self._quality = quality
        return self

    def resolution(self, resolution: str) -> SpriteGenerationBuilder:
        """Sets the resolution setting."""
        self._resolution = resolution
        return self

    def base_asset_id(self, base_asset_id: IdLike) -> SpriteGenerationBuilder:
        """Edits an existing individual image result."""
        self._base_asset_id = base_asset_id
        return self

    def request_id(self, request_id: IdLike) -> SpriteGenerationBuilder:
        """Overrides the idempotency key (defaults to a fresh UUID v4)."""
        self._request_id = request_id
        return self

    def send(self) -> JobCreated:
        """Sends the generation request."""
        return self._dispatch(self._send())

    async def _send(self) -> JobCreated:
        if self._prompt is None:
            raise ConfigError("sprite generation requires a prompt")
        if self._image_model is None:
            raise ConfigError("sprite generation requires an image_model")

        body = {
            "request_id": str(self._request_id or uuid4()),
            "prompt": self._prompt,
            "mode": self._mode.value,
            "image_model": self._image_model,
        }
        if self._text_model is not None:
            body["text_model"] = self._text_model
        if self._quality is not None:
            body["quality"] = self._quality
        if self._resolution is not None:
            body["resolution"] = self._resolution
        if self._base_asset_id is not None:
            body["base_asset_id"] = str(self._base_asset_id)

        return await self._client._send_json(
            JobCreated,
            "POST",
            f"projects/{self._project_id}/generations",
            rate_class=RateClass.TIER1,
            route="POST /projects/{project_id}/generations",
            concurrency=Concurrency.HOLD,
            json_body=body,
        )


class SpritesMixin:
    """Sprite generation and sprite asset endpoints."""

    def generate_sprite(self, project_id: IdLike) -> SpriteGenerationBuilder:
        """Starts building a sprite generation.

        Example::

            job = await (
                client.generate_sprite(project.id)
                .prompt("a red fox, side view")
                .mode(SpriteMode.SINGLE)
                .image_model("openai/gpt-image-2.5-flare")
                .send()
            )
        """
        return SpriteGenerationBuilder(self, self._dispatch, project_id)  # type: ignore[attr-defined]

    async def list_generations(
        self, project_id: IdLike, params: ListParams | None = None
    ) -> GenerationsResponse:
        """Lists a project's generations, including their assets.

        ``GET /projects/{project_id}/generations``
        """
        query = list_query(params or ListParams())
        return await self._send_json(  # type: ignore[attr-defined]
            GenerationsResponse,
            "GET",
            f"projects/{project_id}/generations",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/generations",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def get_generation(
        self, generation_id: IdLike, include_archived: bool = False
    ) -> Generation:
        """Returns one generation and its results.

        ``GET /generations/{id}``
        """
        query = [("include_archived", "true")] if include_archived else None
        return await self._send_json(  # type: ignore[attr-defined]
            Generation,
            "GET",
            f"generations/{generation_id}",
            rate_class=RateClass.TIER2,
            route="GET /generations/{id}",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def list_sprite_assets(
        self, project_id: IdLike, query: str | None = None
    ) -> SpriteAssetsResponse:
        """Searches a project's sprite assets by name or label.

        ``GET /projects/{project_id}/sprite-assets``
        """
        params = [("q", query)] if query is not None else None
        return await self._send_json(  # type: ignore[attr-defined]
            SpriteAssetsResponse,
            "GET",
            f"projects/{project_id}/sprite-assets",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/sprite-assets",
            concurrency=Concurrency.NONE,
            params=params,
        )

    async def get_asset(self, asset_id: IdLike) -> Asset:
        """Returns one sprite asset.

        ``GET /assets/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            Asset,
            "GET",
            f"assets/{asset_id}",
            rate_class=RateClass.TIER2,
            route="GET /assets/{id}",
            concurrency=Concurrency.NONE,
        )

    async def asset_content(self, asset_id: IdLike) -> Download:
        """Returns the trimmed PNG bytes of a sprite asset.

        ``GET /assets/{id}/content``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"assets/{asset_id}/content",
            rate_class=RateClass.TIER2,
            route="GET /assets/{id}/content",
            concurrency=Concurrency.NONE,
        )

    async def asset_original(self, asset_id: IdLike) -> Download:
        """Returns the uncropped original PNG bytes of a sprite asset.

        ``GET /assets/{id}/original``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"assets/{asset_id}/original",
            rate_class=RateClass.TIER2,
            route="GET /assets/{id}/original",
            concurrency=Concurrency.NONE,
        )

    async def rename_asset(self, asset_id: IdLike, name: str | None) -> AssetNameResponse:
        """Renames a sprite asset. Pass ``None`` to clear the name.

        ``PATCH /assets/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetNameResponse,
            "PATCH",
            f"assets/{asset_id}",
            rate_class=RateClass.WRITES,
            route="PATCH /assets/{id}",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def put_asset_metadata(
        self, asset_id: IdLike, metadata: dict[str, str]
    ) -> AssetMetadataResponse:
        """Replaces a sprite asset's metadata.

        ``PUT /assets/{id}/metadata``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AssetMetadataResponse,
            "PUT",
            f"assets/{asset_id}/metadata",
            rate_class=RateClass.WRITES,
            route="PUT /assets/{id}/metadata",
            concurrency=Concurrency.NONE,
            json_body={"metadata": metadata},
        )

    async def archive_asset(self, asset_id: IdLike) -> ArchiveResponse:
        """Archives a sprite asset, hiding it from default lists.

        ``POST /assets/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"assets/{asset_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /assets/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_asset(self, asset_id: IdLike) -> ArchiveResponse:
        """Restores an archived sprite asset.

        ``POST /assets/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"assets/{asset_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /assets/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    async def delete_asset(self, asset_id: IdLike) -> None:
        """Permanently deletes a sprite asset and its original.

        ``DELETE /assets/{id}``
        """
        await self._send_ok(  # type: ignore[attr-defined]
            "DELETE",
            f"assets/{asset_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /assets/{id}",
            concurrency=Concurrency.NONE,
        )

    async def archive_generation(self, generation_id: IdLike) -> ArchiveResponse:
        """Archives a whole generation.

        ``POST /generations/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"generations/{generation_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /generations/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_generation(self, generation_id: IdLike) -> ArchiveResponse:
        """Restores an archived generation.

        ``POST /generations/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"generations/{generation_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /generations/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    async def delete_generation(self, generation_id: IdLike) -> None:
        """Permanently deletes a generation.

        ``DELETE /generations/{id}``
        """
        await self._send_ok(  # type: ignore[attr-defined]
            "DELETE",
            f"generations/{generation_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /generations/{id}",
            concurrency=Concurrency.NONE,
        )

    def stream_generations(
        self, project_id: IdLike, include_archived: bool = False
    ) -> Paginator[Generation]:
        """Streams a project's generations page by page."""

        async def fetch(cursor: str | None) -> Page[Generation]:
            params = ListParams(before=cursor, include_archived=include_archived)
            response = await self.list_generations(project_id, params)
            return Page(
                items=response.generations,
                next_cursor=response.next_cursor,
                total=response.total,
            )

        return Paginator(fetch, self._dispatch)  # type: ignore[attr-defined]


__all__ = ["SpriteGenerationBuilder", "SpritesMixin"]
