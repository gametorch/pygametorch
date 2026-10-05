"""API key models and request builders."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .._models_helpers import DecimalValue, OptionalDecimal
from .._types import ApiKeyScope, SpendResetCadence

__all__ = [
    "ApiKey",
    "ApiKeyWithSecret",
    "CreateApiKeyRequest",
    "KeysResponse",
    "UpdateApiKeyRequest",
]


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ApiKey(BaseModel):
    """An API key (the secret itself is never returned after creation)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str | None = None
    key_prefix: str
    expires_at: datetime | None = None
    max_spend_limit: OptionalDecimal = None
    spend_reset_cadence: str = ""
    key_scope: ApiKeyScope = ApiKeyScope.ADMIN
    project_id: UUID | None = None
    spend: DecimalValue
    lifetime_spend: DecimalValue
    spend_reset_at: datetime | None = None
    created_at: datetime


class ApiKeyWithSecret(ApiKey):
    """Response from ``POST /keys``: an API key plus its secret, shown once."""

    key_full: str

    @property
    def key(self) -> ApiKey:
        """The key metadata, mirroring the Rust SDK's ``created.key``."""
        return self


class KeysResponse(BaseModel):
    """Response from ``GET /keys``."""

    model_config = ConfigDict(extra="ignore")

    keys: list[ApiKey] = []


class CreateApiKeyRequest:
    """Request body for ``POST /keys``.

    Build with one of the scope constructors and chain setters, mirroring the
    Rust SDK:

    .. code-block:: python

        request = (
            CreateApiKeyRequest.project_read(project_id)
            .name("CI read key")
            .max_spend_limit(Decimal(0))
            .spend_reset_cadence(SpendResetCadence.MONTHLY)
            .expires_at(expires_at)
        )
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        expires_at: datetime | None = None,
        max_spend_limit: Decimal | None = None,
        spend_reset_cadence: SpendResetCadence | None = None,
        key_scope: ApiKeyScope | None = None,
        project_id: UUID | None = None,
    ) -> None:
        self._name = name
        self._expires_at = expires_at
        self._max_spend_limit = max_spend_limit
        self._spend_reset_cadence = spend_reset_cadence
        self._key_scope = key_scope
        self._project_id = project_id

    @classmethod
    def new(cls) -> CreateApiKeyRequest:
        """Creates an empty request (which the server treats as an admin key)."""
        return cls()

    @classmethod
    def admin(cls) -> CreateApiKeyRequest:
        """Creates an admin-scoped key request (full account access)."""
        return cls(key_scope=ApiKeyScope.ADMIN)

    @classmethod
    def project_write(cls, project_id: UUID) -> CreateApiKeyRequest:
        """Creates a write-scoped key request bound to ``project_id``."""
        return cls(key_scope=ApiKeyScope.PROJECT_WRITE, project_id=project_id)

    @classmethod
    def project_read(cls, project_id: UUID) -> CreateApiKeyRequest:
        """Creates a read-only key request bound to ``project_id``."""
        return cls(key_scope=ApiKeyScope.PROJECT_READ, project_id=project_id)

    def name(self, name: str) -> CreateApiKeyRequest:
        self._name = name
        return self

    def expires_at(self, expires_at: datetime) -> CreateApiKeyRequest:
        self._expires_at = expires_at
        return self

    def max_spend_limit(self, limit: Decimal) -> CreateApiKeyRequest:
        self._max_spend_limit = limit
        return self

    def spend_reset_cadence(self, cadence: SpendResetCadence) -> CreateApiKeyRequest:
        self._spend_reset_cadence = cadence
        return self

    def key_scope(self, scope: ApiKeyScope) -> CreateApiKeyRequest:
        self._key_scope = scope
        return self

    def project_id(self, project_id: UUID) -> CreateApiKeyRequest:
        self._project_id = project_id
        return self

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self._name is not None:
            body["name"] = self._name
        if self._expires_at is not None:
            body["expires_at"] = _format_datetime(self._expires_at)
        if self._max_spend_limit is not None:
            body["max_spend_limit"] = str(self._max_spend_limit)
        if self._spend_reset_cadence is not None:
            body["spend_reset_cadence"] = self._spend_reset_cadence.value
        if self._key_scope is not None:
            body["key_scope"] = self._key_scope.value
        if self._project_id is not None:
            body["project_id"] = str(self._project_id)
        return body


class UpdateApiKeyRequest:
    """Request body for ``PATCH /keys/{id}``. Only set fields are updated."""

    def __init__(
        self,
        *,
        name: str | None = None,
        expires_at: datetime | None = None,
        max_spend_limit: Decimal | None = None,
        spend_reset_cadence: SpendResetCadence | None = None,
    ) -> None:
        self._name = name
        self._expires_at = expires_at
        self._max_spend_limit = max_spend_limit
        self._spend_reset_cadence = spend_reset_cadence

    @classmethod
    def new(cls) -> UpdateApiKeyRequest:
        """Creates an empty request."""
        return cls()

    def name(self, name: str) -> UpdateApiKeyRequest:
        self._name = name
        return self

    def expires_at(self, expires_at: datetime) -> UpdateApiKeyRequest:
        self._expires_at = expires_at
        return self

    def max_spend_limit(self, limit: Decimal) -> UpdateApiKeyRequest:
        self._max_spend_limit = limit
        return self

    def spend_reset_cadence(self, cadence: SpendResetCadence) -> UpdateApiKeyRequest:
        self._spend_reset_cadence = cadence
        return self

    def to_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self._name is not None:
            body["name"] = self._name
        if self._expires_at is not None:
            body["expires_at"] = _format_datetime(self._expires_at)
        if self._max_spend_limit is not None:
            body["max_spend_limit"] = str(self._max_spend_limit)
        if self._spend_reset_cadence is not None:
            body["spend_reset_cadence"] = self._spend_reset_cadence.value
        return body
