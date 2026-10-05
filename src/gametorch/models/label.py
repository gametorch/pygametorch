"""Label models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .provenance import ProvenanceFields

__all__ = [
    "Label",
    "LabelAsset",
    "LabelAssociation",
    "LabelItems",
    "LabelSavedAnimation",
    "LabelSound",
    "LabelsResponse",
]


class Label(BaseModel):
    """A project label (OpenAPI ``LabelRow``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    color: str | None = None
    thumbnail_asset_id: UUID | None = None
    created_at: datetime


class LabelsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/labels``."""

    model_config = ConfigDict(extra="ignore")

    labels: list[Label] = []


class LabelAssociation(BaseModel):
    """The label-name set returned by a label mutation."""

    model_config = ConfigDict(extra="ignore")

    ok: bool = True
    labels: list[str] = []


class LabelAsset(ProvenanceFields):
    """A sprite asset as returned by the label-items endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    width: int = 0
    height: int = 0
    name: str | None = None
    labels: list[str] = []
    metadata: dict[str, str] = {}
    has_original: bool = False
    generation_id: UUID | None = None
    prompt: str | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None


class LabelSound(ProvenanceFields):
    """A sound asset as returned by the label-items endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    format: str = ""
    name: str | None = None
    labels: list[str] = []
    metadata: dict[str, str] = {}
    generation_id: UUID | None = None
    prompt: str | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None


class LabelSavedAnimation(ProvenanceFields):
    """A saved animation as returned by the label-items endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    project_id: UUID
    generation_id: UUID
    start_frame: int
    end_frame: int
    name: str | None = None
    animation_model: str | None = None
    prompt: str | None = None
    base_asset_id: UUID | None = None
    frame_count: int = 0
    labels: list[str] = []
    metadata: dict[str, str] = {}
    created_at: datetime | None = None
    archived_at: datetime | None = None


class LabelItems(BaseModel):
    """Response from ``GET /labels/{label_id}/items``."""

    model_config = ConfigDict(extra="ignore")

    label: Label
    assets: list[LabelAsset] = []
    sounds: list[LabelSound] = []
    saved_animations: list[LabelSavedAnimation] = []
