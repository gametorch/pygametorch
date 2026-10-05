"""Project endpoints."""

from __future__ import annotations

from .._rate_limit import Concurrency, RateClass
from .._types import OkResponse
from ..models import Project, ProjectsResponse


class ProjectsMixin:
    """Project lifecycle endpoints."""

    async def list_projects(self) -> ProjectsResponse:
        """Lists the projects in the caller's scope.

        ``GET /projects``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ProjectsResponse,
            "GET",
            "projects",
            rate_class=RateClass.TIER2,
            route="GET /projects",
            concurrency=Concurrency.NONE,
        )

    async def create_project(self, name: str) -> Project:
        """Creates a project owned by the caller's scope.

        ``POST /projects``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            Project,
            "POST",
            "projects",
            rate_class=RateClass.WRITES,
            route="POST /projects",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def rename_project(self, slug: str, name: str) -> Project:
        """Renames a project. The slug may change.

        ``PATCH /projects/{slug}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            Project,
            "PATCH",
            f"projects/{slug}",
            rate_class=RateClass.WRITES,
            route="PATCH /projects/{slug}",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def delete_project(self, slug: str) -> OkResponse:
        """Permanently deletes a project and its generations and assets.

        ``DELETE /projects/{slug}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"projects/{slug}",
            rate_class=RateClass.WRITES,
            route="DELETE /projects/{slug}",
            concurrency=Concurrency.NONE,
        )


__all__ = ["ProjectsMixin"]
