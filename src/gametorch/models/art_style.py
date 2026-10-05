"""Art style models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = ["ArtStyle", "ArtStyleSuggestion", "ArtStylesResponse"]


class ArtStyle(BaseModel):
    """A reusable project art style."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    created_at: datetime


class ArtStylesResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/art-styles``."""

    model_config = ConfigDict(extra="ignore")

    art_styles: list[ArtStyle] = []


class ArtStyleSuggestion(BaseModel):
    """A freshly generated art-style suggestion."""

    model_config = ConfigDict(extra="ignore")

    name: str
