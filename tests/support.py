"""Shared helpers for the live test suites."""

from __future__ import annotations

import os
from uuid import uuid4

from gametorch import ApiError, AsyncClient, Project

ENV_API_KEY = "GAMETORCH_API_KEY"
ENV_BASE_URL = "GAMETORCH_BASE_URL"
ENV_KEEP_PROJECT = "GAMETORCH_KEEP_PROJECT"
ENV_LIVE_WRITES = "GAMETORCH_LIVE_WRITES"
ENV_LIVE_SPEND = "GAMETORCH_LIVE_SPEND"


def has_api_key() -> bool:
    return bool(os.environ.get(ENV_API_KEY))


def live_params() -> dict[str, str]:
    """Credentials and base URL for a live client."""
    params = {"api_key": os.environ[ENV_API_KEY]}
    if os.environ.get(ENV_BASE_URL):
        params["base_url"] = os.environ[ENV_BASE_URL]
    return params


def live_writes_enabled() -> bool:
    return os.environ.get(ENV_LIVE_WRITES) == "1"


def live_spend_enabled() -> bool:
    return os.environ.get(ENV_LIVE_SPEND) == "1"


def keep_project() -> bool:
    return os.environ.get(ENV_KEEP_PROJECT) == "1"


def short_name(prefix: str) -> str:
    """A short, unique, label-safe name (letters, numbers, dashes only)."""
    return f"{prefix}-{uuid4().hex[:8]}"


def project_name(kind: str) -> str:
    return f"SDK {kind} {uuid4().hex[:8]}"


async def create_project_or_none(client: AsyncClient, kind: str) -> Project | None:
    """Creates a fresh project, or returns ``None`` if the key may not."""
    try:
        project = await client.create_project(project_name(kind))
    except ApiError as err:
        if err.is_forbidden():
            return None
        raise
    print(f"created project '{project.name}' ({project.slug})")
    return project


async def finish_project(client: AsyncClient, slug: str) -> None:
    """Deletes the project unless ``GAMETORCH_KEEP_PROJECT=1``."""
    if keep_project():
        print(f"keeping project '{slug}' (GAMETORCH_KEEP_PROJECT=1)")
    else:
        await client.delete_project(slug)
        print(f"deleted project '{slug}'")
