"""Catalog models: available sprite, sound and animation models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .._models_helpers import OptionalDecimal

__all__ = [
    "AnimationModelInfo",
    "AnimationModels",
    "ImageModel",
    "MultipleLayout",
    "SoundModelInfo",
    "SoundModels",
    "SpriteModels",
    "TextModel",
]


class MultipleLayout(BaseModel):
    """Layout metadata for sprite ``multiple`` mode."""

    model_config = ConfigDict(extra="ignore")

    columns: int
    images_per_request: int
    rows: int


class ImageModel(BaseModel):
    """An image model available for sprite generation."""

    model_config = ConfigDict(extra="ignore")

    available: bool
    blurb: str = ""
    capabilities_url: str | None = None
    default_canvas_size: str | None = None
    default_quality: str | None = None
    default_resolution: str | None = None
    editing: bool
    id: str
    name: str
    native_transparency: bool
    qualities: list[str] = []
    reservation_credits: OptionalDecimal = None
    resolutions: list[str] = []
    transparency_status: str | None = None
    unavailable_reason: str | None = None


class TextModel(BaseModel):
    """A prompt-enhancement text model."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class SpriteModels(BaseModel):
    """Response from ``GET /sprite-models`` (OpenAPI ``SpriteCatalog``)."""

    model_config = ConfigDict(extra="ignore")

    default_text_model: str
    empirical_evidence: str | None = None
    image_models: list[ImageModel] = []
    modes: list[str] = []
    multiple_layout: MultipleLayout
    reservation_credits: OptionalDecimal = None
    resolution_note: str | None = None
    resolution_scope: str | None = None
    text_models: list[TextModel] = []
    verified_at: str | None = None


class SoundModelInfo(BaseModel):
    """A sound generation model."""

    model_config = ConfigDict(extra="ignore")

    blurb: str = ""
    id: str
    name: str


class SoundModels(BaseModel):
    """Response from ``GET /sound-models`` (OpenAPI ``SoundCatalog``)."""

    model_config = ConfigDict(extra="ignore")

    default_format: str
    formats: list[str] = []
    model: SoundModelInfo


class AnimationModelInfo(BaseModel):
    """An animation model addressed by its public name (``ash`` etc.)."""

    model_config = ConfigDict(extra="ignore")

    description: str = ""
    id: str
    name: str
    supported_durations: list[int] = []
    supported_resolutions: list[str] = []


class AnimationModels(BaseModel):
    """Response from ``GET /animation-models`` (OpenAPI ``AnimationCatalog``)."""

    model_config = ConfigDict(extra="ignore")

    data: list[AnimationModelInfo] = []
