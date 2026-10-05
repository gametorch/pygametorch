"""Project models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = ["Project", "ProjectsResponse"]


class Project(BaseModel):
    """A GameTorch project."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    slug: str
    created_at: datetime


class ProjectsResponse(BaseModel):
    """Response from ``GET /projects``."""

    model_config = ConfigDict(extra="ignore")

    projects: list[Project] = []
