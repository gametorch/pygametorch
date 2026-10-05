"""Saved animation models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = ["SavedAnimation", "SavedAnimationsResponse"]


class SavedAnimation(BaseModel):
    """A named frame range taken from an animation run, reusable as a preset."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    project_id: UUID
    generation_id: UUID
    name: str | None = None
    animation_model: str | None = None
    prompt: str | None = None
    base_asset_id: UUID | None = None
    start_frame: int
    end_frame: int
    frame_count: int = 0
    labels: list[str] = []
    metadata: dict[str, str] = {}
    created_at: datetime
    archived_at: datetime | None = None


class SavedAnimationsResponse(BaseModel):
    """Response from ``GET /projects/{project_id}/saved-animations``."""

    model_config = ConfigDict(extra="ignore")

    saved_animations: list[SavedAnimation] = []
    next_cursor: str | None = None
    total: int = 0
