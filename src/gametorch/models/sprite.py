"""Sprite generation and asset models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .._models_helpers import BoolOrInt, DecimalValue, StringListLenient
from .provenance import ProvenanceFields

__all__ = ["Asset", "Generation", "GenerationsResponse", "SpriteAssetsResponse"]


class Asset(ProvenanceFields):
    """A sprite asset (OpenAPI ``SpriteAsset``).

    Some fields are absent depending on the endpoint, for example nested assets
    in a generation omit ``generation_id`` and ``created_at``.
    """

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str | None = None
    width: int = 0
    height: int = 0
    labels: list[str] = []
    metadata: dict[str, str] = {}
    has_original: bool = False
    dismissed_suggestions: StringListLenient = []
    generation_id: UUID | None = None
    project_id: UUID | None = None
    prompt: str | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None


class Generation(ProvenanceFields):
    """A sprite generation and its results (OpenAPI ``SpriteGeneration``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    project_id: UUID
    prompt: str
    mode: str
    image_model: str
    text_model: str | None = None
    quality: str | None = None
    resolution: str | None = None
    base_asset_id: UUID | None = None
    status: str
    credits_consumed: DecimalValue
    reserved_credits: DecimalValue
    assets_delivered: BoolOrInt = 0
    archived_assets: int = 0
    warming: bool = False
    error: str | None = None
    label_suggestions: StringListLenient = []
    art_style_suggestion: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    assets: list[Asset] = []


class GenerationsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/generations``."""

    model_config = ConfigDict(extra="ignore")

    generations: list[Generation] = []
    next_cursor: str | None = None
    total: int = 0


class SpriteAssetsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/sprite-assets``."""

    model_config = ConfigDict(extra="ignore")

    assets: list[Asset] = []
