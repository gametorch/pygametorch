"""Animation run, frame and export models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .._models_helpers import BoolOrInt, DecimalValue
from .._types import Download
from .provenance import ProvenanceFields

__all__ = [
    "AnimationAsset",
    "AnimationEstimate",
    "AnimationFrame",
    "AnimationRun",
    "AnimationsResponse",
    "Export",
    "ExportFrame",
    "ExportPlan",
    "ExportReference",
    "FrameRun",
    "GodotExport",
    "TexturePackerExport",
]


class AnimationAsset(BaseModel):
    """Metadata about the underlying animation clip (OpenAPI ``AnimationAsset``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    duration_seconds: int = 0
    resolution: str = ""
    created_at: datetime


class FrameRun(BaseModel):
    """A frame-generation run that sampled an animation into PNG frames."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    status: str
    fps: int = 0
    frame_count: int = 0
    warming: bool = False
    credits_consumed: DecimalValue
    reserved_credits: DecimalValue
    error: str | None = None
    created_at: datetime


class AnimationFrame(BaseModel):
    """An individual generated animation frame (OpenAPI ``AnimationFrame``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    frame_number: int
    generation_id: UUID | None = None
    created_at: datetime


class AnimationRun(ProvenanceFields):
    """An animation run and its results (OpenAPI ``AnimationGeneration``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    project_id: UUID
    prompt: str
    animation_model: str | None = None
    duration: int | None = None
    animation: AnimationAsset | None = None
    status: str
    credits_consumed: DecimalValue
    reserved_credits: DecimalValue
    assets_delivered: BoolOrInt = 0
    base_asset_id: UUID | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    frame_runs: list[FrameRun] = []
    frames: list[AnimationFrame] = []


class AnimationsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/animation-runs``."""

    model_config = ConfigDict(extra="ignore")

    animations: list[AnimationRun] = []
    next_cursor: str | None = None
    total: int = 0


class AnimationEstimate(BaseModel):
    """Response from ``POST /projects/{project_id}/animation-runs/estimate``."""

    model_config = ConfigDict(extra="ignore")

    animation_model: str
    duration: int = 0
    resolution: str = ""
    credits: DecimalValue
    usd: DecimalValue
    reserved_credits: DecimalValue


class ExportReference(BaseModel):
    """The reference frame used to size an export canvas."""

    model_config = ConfigDict(extra="ignore")

    bounds: list[int] = []
    image_width: int
    image_height: int


class ExportFrame(BaseModel):
    """Layout information for a single exported frame."""

    model_config = ConfigDict(extra="ignore")

    frame_number: int
    bounds: list[int] | None = None
    image_width: int
    image_height: int
    offset_x: int | None = None
    offset_y: int | None = None
    scaled_width: int | None = None
    scaled_height: int | None = None


class ExportPlan(BaseModel):
    """Response from ``POST /animation-runs/{id}/export-plan``."""

    model_config = ConfigDict(extra="ignore")

    start_frame: int
    end_frame: int
    reference: ExportReference | None = None
    first_frame: ExportFrame | None = None
    frames: list[ExportFrame] = []
    max_width: int
    max_height: int
    scale: float
    scale_width: float
    scale_height: float
    canvas_width: int
    canvas_height: int
    frame_count: int


class TexturePackerExport(BaseModel):
    """The JSON body returned by the TexturePacker export endpoint."""

    model_config = ConfigDict(extra="ignore")

    plan: ExportPlan
    texturepacker: Any = None
    image_base64: str
    image_filename: str
    json_filename: str


class GodotExport(BaseModel):
    """The JSON body returned by the Godot export endpoint."""

    model_config = ConfigDict(extra="ignore")

    plan: ExportPlan
    tres: str
    image_base64: str
    image_filename: str
    tres_filename: str


@dataclass
class Export:
    """The result of :meth:`~gametorch.AsyncClient.export`, which varies by format.

    Exactly one of :attr:`texturepacker`, :attr:`godot` or :attr:`binary` is set.
    """

    texturepacker: TexturePackerExport | None = None
    godot: GodotExport | None = None
    binary: Download | None = None

    def is_binary(self) -> bool:
        """Whether this is a binary export."""
        return self.binary is not None

    def as_binary(self) -> Download | None:
        """Returns the binary payload, if this is a binary export."""
        return self.binary

    def into_binary(self) -> Download | None:
        """Returns the binary payload, if this is a binary export."""
        return self.binary
