"""Shared types used across the SDK: pagination, request parameters, downloads
and the common acknowledgement/creation envelopes.
"""

from __future__ import annotations

import collections
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ._models_helpers import DecimalValue

__all__ = [
    "ApiKeyScope",
    "ArchiveResponse",
    "AssetMetadataResponse",
    "AssetNameResponse",
    "Download",
    "ExportFormat",
    "JobCreated",
    "ListParams",
    "OkResponse",
    "Page",
    "Paginator",
    "SpendResetCadence",
    "SpriteMode",
    "credits_to_usd",
]


class SpriteMode(StrEnum):
    """Sprite generation mode."""

    SINGLE = "single"
    MULTIPLE = "multiple"


class ExportFormat(StrEnum):
    """The supported animation export formats."""

    TEXTURE_PACKER = "texturepacker"
    TEXTURE_PACKER_ZIP = "texturepacker.zip"
    ASEPRITE = "aseprite"
    GODOT = "godot"
    GODOT_ZIP = "godot.zip"
    GRID = "grid"
    GAME_MAKER = "gamemaker"
    SEQUENCE_ZIP = "sequence.zip"

    def as_str(self) -> str:
        """The path segment used by the export endpoint."""
        return self.value


class ApiKeyScope(StrEnum):
    """What an API key is allowed to do. The scope is fixed at creation."""

    ADMIN = "admin"
    PROJECT_WRITE = "project_write"
    PROJECT_READ = "project_read"

    def as_str(self) -> str:
        return self.value


class SpendResetCadence(StrEnum):
    """How often an API key's spend counter resets."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"

    def as_str(self) -> str:
        return self.value


def credits_to_usd(credits: Decimal) -> Decimal:
    """Converts GameTorch credits to US dollars (100 credits = $1)."""
    return credits / Decimal(100)


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class OkResponse(_Base):
    """A generic acknowledgement response (OpenAPI ``OkResponse``)."""

    ok: bool = True


class ArchiveResponse(_Base):
    """Response returned by archive/unarchive endpoints."""

    ok: bool = True
    archived_at: datetime | None = None


class AssetNameResponse(_Base):
    """Response returned by asset rename endpoints."""

    ok: bool = True
    name: str | None = None


class AssetMetadataResponse(_Base):
    """Response returned by metadata endpoints."""

    ok: bool = True
    metadata: dict[str, str] = {}


class JobCreated(_Base):
    """A job-creation envelope returned by generation endpoints."""

    id: UUID
    status: str
    created: bool
    reserved_credits: DecimalValue


@dataclass
class Download:
    """Raw bytes returned by a content endpoint plus the response content type."""

    content_type: str | None
    data: bytes

    def as_bytes(self) -> bytes:
        return self.data

    def into_bytes(self) -> bytes:
        return self.data

    def len(self) -> int:
        return len(self.data)

    def is_empty(self) -> bool:
        return not self.data

    def __len__(self) -> int:
        return len(self.data)

    def __bool__(self) -> bool:
        return bool(self.data)


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """One page of a paginated list response."""

    items: list[T]
    next_cursor: str | None
    total: int


PageFetcher = Callable[[str | None], Awaitable[Page[T]]]


class Paginator(Generic[T]):
    """An asynchronous (or synchronous) cursor over a paginated list endpoint.

    The same object supports ``async for`` when produced by
    :class:`~gametorch.AsyncClient` and plain ``for`` when produced by
    :class:`~gametorch.Client`.
    """

    def __init__(self, fetch: PageFetcher[T], dispatch: Callable[[Awaitable[Any]], Any]) -> None:
        self._fetch = fetch
        self._dispatch = dispatch
        self._cursor: str | None = None
        self._finished = False
        self._buffer: collections.deque[T] = collections.deque()
        self._total: int | None = None

    async def _next_page(self) -> list[T] | None:
        if self._finished:
            return None
        page = await self._fetch(self._cursor)
        self._total = page.total
        self._cursor = page.next_cursor
        if self._cursor is None:
            self._finished = True
        if not page.items and self._finished:
            return None
        return page.items

    def next_page(self) -> Any:
        """Fetches the next page, or ``None`` when the cursor is exhausted."""
        return self._dispatch(self._next_page())

    async def _next_item(self) -> T | None:
        while True:
            if self._buffer:
                return self._buffer.popleft()
            items = await self._next_page()
            if items is None:
                return None
            self._buffer.extend(items)

    def next_item(self) -> Any:
        """Fetches the next item, transparently loading pages as needed."""
        return self._dispatch(self._next_item())

    @property
    def total(self) -> int | None:
        """The total number of items reported by the API, once known."""
        return self._total

    def __aiter__(self) -> Paginator[T]:
        return self

    async def __anext__(self) -> T:
        item = await self._next_item()
        if item is None:
            raise StopAsyncIteration
        return item

    def __iter__(self) -> Paginator[T]:
        return self

    def __next__(self) -> T:
        item = self._dispatch(self._next_item())
        if item is None:
            raise StopIteration
        return item


@dataclass
class ListParams:
    """Options shared by the paginated list endpoints."""

    before: str | None = None
    include_archived: bool = False
    base_asset_id: UUID | None = None

    @classmethod
    def new(cls) -> ListParams:
        """Creates empty list parameters."""
        return cls()

    def with_before(self, cursor: str) -> ListParams:
        self.before = cursor
        return self

    def with_include_archived(self, include: bool = True) -> ListParams:
        self.include_archived = include
        return self

    def with_base_asset_id(self, base_asset_id: UUID) -> ListParams:
        self.base_asset_id = base_asset_id
        return self
