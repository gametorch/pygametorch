"""Endpoint implementations, grouped by resource.

Each submodule contains a mixin class with methods for one area of the API.
:class:`~gametorch.AsyncClient` inherits them all, so every method is available
on the client.
"""

from __future__ import annotations

from .._types import ListParams

__all__ = ["list_query"]


def list_query(params: ListParams) -> list[tuple[str, str]]:
    """Builds the shared ``before`` / ``include_archived`` query pairs."""
    query: list[tuple[str, str]] = []
    if params.before is not None:
        query.append(("before", params.before))
    if params.include_archived:
        query.append(("include_archived", "true"))
    return query
