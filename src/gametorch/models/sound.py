"""Sound generation and asset models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .._models_helpers import BoolOrInt, DecimalValue, StringListLenient
from .provenance import ProvenanceFields

__all__ = ["SoundAsset", "SoundGeneration", "SoundGenerationsResponse"]


class SoundAsset(ProvenanceFields):
    """A sound asset (OpenAPI ``SoundAsset``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    format: str = ""
    name: str | None = None
    labels: list[str] = []
    metadata: dict[str, str] = {}
    dismissed_suggestions: StringListLenient = []
    created_at: datetime | None = None
    archived_at: datetime | None = None


class SoundGeneration(ProvenanceFields):
    """A sound generation and its results (OpenAPI ``SoundGeneration``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    project_id: UUID
    prompt: str
    sound_model: str
    response_format: str | None = None
    status: str
    credits_consumed: DecimalValue
    reserved_credits: DecimalValue
    assets_delivered: BoolOrInt = 0
    archived_assets: int = 0
    error: str | None = None
    label_suggestions: StringListLenient = []
    created_at: datetime
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    assets: list[SoundAsset] = []


class SoundGenerationsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/sound-generations``."""

    model_config = ConfigDict(extra="ignore")

    sound_generations: list[SoundGeneration] = []
    next_cursor: str | None = None
    total: int = 0
