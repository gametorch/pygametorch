"""Animation run, frame generation and content endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from .._errors import ConfigError
from .._rate_limit import Concurrency, RateClass
from .._types import (
    ArchiveResponse,
    Download,
    JobCreated,
    ListParams,
    Page,
    Paginator,
)
from ..models import AnimationEstimate, AnimationRun, AnimationsResponse
from . import list_query

IdLike = UUID | str


class AnimationEstimateBuilder:
    """Builder for an animation cost estimate."""

    def __init__(self, client, dispatch, project_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._animation_model: str | None = None
        self._duration: int | None = None
        self._base_asset_id: IdLike | None = None

    def animation_model(self, animation_model: str) -> AnimationEstimateBuilder:
        """Sets the animation model (``ash``, ``birch`` or ``cedar``); required."""
        self._animation_model = animation_model
        return self

    def duration(self, duration: int) -> AnimationEstimateBuilder:
        """Sets the desired duration in seconds."""
        self._duration = duration
        return self

    def base_asset_id(self, base_asset_id: IdLike) -> AnimationEstimateBuilder:
        """Bases the estimate on an existing asset."""
        self._base_asset_id = base_asset_id
        return self

    def send(self) -> AnimationEstimate:
        """Sends the estimate request."""
        return self._dispatch(self._send())

    async def _send(self) -> AnimationEstimate:
        if self._animation_model is None:
            raise ConfigError("animation estimate requires an animation_model")
        body: dict[str, object] = {"animation_model": self._animation_model}
        if self._duration is not None:
            body["duration"] = self._duration
        if self._base_asset_id is not None:
            body["base_asset_id"] = str(self._base_asset_id)
        return await self._client._send_json(
            AnimationEstimate,
            "POST",
            f"projects/{self._project_id}/animation-runs/estimate",
            rate_class=RateClass.TIER2,
            route="POST /projects/{project_id}/animation-runs/estimate",
            concurrency=Concurrency.NONE,
            json_body=body,
        )


class AnimationRunBuilder:
    """Builder for an animation run."""

    def __init__(self, client, dispatch, project_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._prompt: str | None = None
        self._animation_model: str | None = None
        self._duration: int | None = None
        self._base_asset_id: IdLike | None = None
        self._request_id: IdLike | None = None

    def prompt(self, prompt: str) -> AnimationRunBuilder:
        """Sets the generation prompt (required)."""
        self._prompt = prompt
        return self

    def animation_model(self, animation_model: str) -> AnimationRunBuilder:
        """Sets the animation model (``ash``, ``birch`` or ``cedar``); required."""
        self._animation_model = animation_model
        return self

    def duration(self, duration: int) -> AnimationRunBuilder:
        """Sets the desired duration in seconds."""
        self._duration = duration
        return self

    def base_asset_id(self, base_asset_id: IdLike) -> AnimationRunBuilder:
        """Animates an existing asset."""
        self._base_asset_id = base_asset_id
        return self

    def request_id(self, request_id: IdLike) -> AnimationRunBuilder:
        """Overrides the idempotency key (defaults to a fresh UUID v4)."""
        self._request_id = request_id
        return self

    def send(self) -> JobCreated:
        """Sends the animation run request."""
        return self._dispatch(self._send())

    async def _send(self) -> JobCreated:
        if self._prompt is None:
            raise ConfigError("animation run requires a prompt")
        if self._animation_model is None:
            raise ConfigError("animation run requires an animation_model")
        body: dict[str, object] = {
            "request_id": str(self._request_id or uuid4()),
            "prompt": self._prompt,
            "animation_model": self._animation_model,
        }
        if self._duration is not None:
            body["duration"] = self._duration
        if self._base_asset_id is not None:
            body["base_asset_id"] = str(self._base_asset_id)
        return await self._client._send_json(
            JobCreated,
            "POST",
            f"projects/{self._project_id}/animation-runs",
            rate_class=RateClass.TIER1,
            route="POST /projects/{project_id}/animation-runs",
            concurrency=Concurrency.HOLD,
            json_body=body,
        )


class FrameGenerationBuilder:
    """Builder for animation frame generation."""

    def __init__(self, client, dispatch, project_id: IdLike, run_id: IdLike) -> None:
        self._client = client
        self._dispatch = dispatch
        self._project_id = project_id
        self._run_id = run_id
        self._fps: int = 12
        self._request_id: IdLike | None = None

    def fps(self, fps: int) -> FrameGenerationBuilder:
        """Sets the sampling rate (1-30 fps). Defaults to 12."""
        self._fps = fps
        return self

    def request_id(self, request_id: IdLike) -> FrameGenerationBuilder:
        """Overrides the idempotency key (defaults to a fresh UUID v4)."""
        self._request_id = request_id
        return self

    def send(self) -> JobCreated:
        """Sends the frame-generation request."""
        return self._dispatch(self._send())

    async def _send(self) -> JobCreated:
        body = {
            "request_id": str(self._request_id or uuid4()),
            "fps": self._fps,
        }
        return await self._client._send_json(
            JobCreated,
            "POST",
            f"projects/{self._project_id}/animation-runs/{self._run_id}/frames",
            rate_class=RateClass.TIER1,
            route="POST /projects/{project_id}/animation-runs/{id}/frames",
            concurrency=Concurrency.FRAME_GENERATION,
            json_body=body,
        )


class AnimationsMixin:
    """Animation run, frame generation and content endpoints."""

    def estimate_animation(self, project_id: IdLike) -> AnimationEstimateBuilder:
        """Estimates the credit cost of an animation run without starting one.

        ``POST /projects/{project_id}/animation-runs/estimate``
        """
        return AnimationEstimateBuilder(self, self._dispatch, project_id)  # type: ignore[attr-defined]

    def generate_animation(self, project_id: IdLike) -> AnimationRunBuilder:
        """Starts building an animation run."""
        return AnimationRunBuilder(self, self._dispatch, project_id)  # type: ignore[attr-defined]

    async def list_animation_runs(
        self, project_id: IdLike, params: ListParams | None = None
    ) -> AnimationsResponse:
        """Lists a project's animation runs.

        ``GET /projects/{project_id}/animation-runs``
        """
        params = params or ListParams()
        query = list_query(params)
        if params.base_asset_id is not None:
            query.append(("base_asset_id", str(params.base_asset_id)))
        return await self._send_json(  # type: ignore[attr-defined]
            AnimationsResponse,
            "GET",
            f"projects/{project_id}/animation-runs",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/animation-runs",
            concurrency=Concurrency.NONE,
            params=query,
        )

    async def get_animation_run(self, run_id: IdLike) -> AnimationRun:
        """Returns one animation run and its frames.

        ``GET /animation-runs/{id}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AnimationRun,
            "GET",
            f"animation-runs/{run_id}",
            rate_class=RateClass.TIER2,
            route="GET /animation-runs/{id}",
            concurrency=Concurrency.NONE,
        )

    async def animation_content(self, run_id: IdLike) -> Download:
        """Returns the animation clip bytes.

        ``GET /animation-runs/{id}/content``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"animation-runs/{run_id}/content",
            rate_class=RateClass.TIER2,
            route="GET /animation-runs/{id}/content",
            concurrency=Concurrency.NONE,
        )

    async def archive_animation_run(self, run_id: IdLike) -> ArchiveResponse:
        """Archives an animation run.

        ``POST /animation-runs/{id}/archive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"animation-runs/{run_id}/archive",
            rate_class=RateClass.WRITES,
            route="POST /animation-runs/{id}/archive",
            concurrency=Concurrency.NONE,
        )

    async def unarchive_animation_run(self, run_id: IdLike) -> ArchiveResponse:
        """Restores an archived animation run.

        ``POST /animation-runs/{id}/unarchive``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ArchiveResponse,
            "POST",
            f"animation-runs/{run_id}/unarchive",
            rate_class=RateClass.WRITES,
            route="POST /animation-runs/{id}/unarchive",
            concurrency=Concurrency.NONE,
        )

    async def delete_animation_run(self, run_id: IdLike) -> None:
        """Permanently deletes an animation run.

        ``DELETE /animation-runs/{id}``
        """
        await self._send_ok(  # type: ignore[attr-defined]
            "DELETE",
            f"animation-runs/{run_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /animation-runs/{id}",
            concurrency=Concurrency.NONE,
        )

    def generate_frames(self, project_id: IdLike, run_id: IdLike) -> FrameGenerationBuilder:
        """Generates individual PNG frames from a finished animation run.

        ``POST /projects/{project_id}/animation-runs/{id}/frames``
        """
        return FrameGenerationBuilder(self, self._dispatch, project_id, run_id)  # type: ignore[attr-defined]

    async def frame_content(self, frame_id: IdLike) -> Download:
        """Returns the PNG bytes of a generated frame by its id.

        ``GET /animation-run-frames/{id}/content``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"animation-run-frames/{frame_id}/content",
            rate_class=RateClass.TIER2,
            route="GET /animation-run-frames/{id}/content",
            concurrency=Concurrency.NONE,
        )

    async def frame_content_by_number(self, run_id: IdLike, frame_number: int) -> Download:
        """Returns the PNG bytes of a frame addressed by its 1-based number.

        ``GET /animation-runs/{id}/frames/{number}/content``
        """
        return await self._send_download(  # type: ignore[attr-defined]
            "GET",
            f"animation-runs/{run_id}/frames/{frame_number}/content",
            rate_class=RateClass.TIER2,
            route="GET /animation-runs/{id}/frames/{number}/content",
            concurrency=Concurrency.NONE,
        )

    def stream_animation_runs(
        self, project_id: IdLike, params: ListParams | None = None
    ) -> Paginator[AnimationRun]:
        """Streams a project's animation runs page by page, honoring filters."""
        base_params = params or ListParams()

        async def fetch(cursor: str | None) -> Page[AnimationRun]:
            page_params = ListParams(
                before=cursor,
                include_archived=base_params.include_archived,
                base_asset_id=base_params.base_asset_id,
            )
            response = await self.list_animation_runs(project_id, page_params)
            return Page(
                items=response.animations,
                next_cursor=response.next_cursor,
                total=response.total,
            )

        return Paginator(fetch, self._dispatch)  # type: ignore[attr-defined]


__all__ = [
    "AnimationEstimateBuilder",
    "AnimationRunBuilder",
    "AnimationsMixin",
    "FrameGenerationBuilder",
]
