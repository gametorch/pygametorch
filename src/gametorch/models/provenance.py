"""Provenance metadata shared by generated resources."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = ["Provenance", "ProvenanceFields"]


class Provenance(BaseModel):
    """Who or what created a resource.

    GameTorch records the Clerk user and, when the request came through an API
    key, the key that ran the operation. These fields are flattened onto the
    owning resource, so they appear as ``user_id``, ``source``, ``api_key_id``
    and ``key_name`` on the resource itself.
    """

    model_config = ConfigDict(extra="ignore")

    user_id: str | None = None
    source: str | None = None
    api_key_id: UUID | None = None
    key_name: str | None = None


class ProvenanceFields(BaseModel):
    """Mixin adding the flattened provenance fields plus a ``provenance`` view."""

    model_config = ConfigDict(extra="ignore")

    user_id: str | None = None
    source: str | None = None
    api_key_id: UUID | None = None
    key_name: str | None = None

    @property
    def provenance(self) -> Provenance:
        """The provenance fields grouped into a :class:`Provenance` object."""
        return Provenance(
            user_id=self.user_id,
            source=self.source,
            api_key_id=self.api_key_id,
            key_name=self.key_name,
        )
