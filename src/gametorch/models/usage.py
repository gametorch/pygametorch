"""Usage and spending models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .._models_helpers import DecimalMap, DecimalValue, OptionalDecimal

__all__ = [
    "HistogramBucket",
    "Usage",
    "UsageHistogram",
    "UsageHistogramSource",
    "UsageRecord",
    "UsageSummary",
]


class UsageSummary(BaseModel):
    """A per-source spend summary entry (OpenAPI ``UsageSummaryEntry``)."""

    model_config = ConfigDict(extra="ignore")

    source: str
    api_key_id: UUID | None = None
    user_id: str | None = None
    key_name: str | None = None
    credits_consumed: DecimalValue


class UsageRecord(BaseModel):
    """A single operation-log entry (OpenAPI ``UsageRecord``)."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    generation_id: UUID | None = None
    created_at: datetime
    source: str
    operation: str | None = None
    api_key_id: UUID | None = None
    user_id: str | None = None
    model: str | None = None
    credits_consumed: DecimalValue
    settled: bool | None = None
    generation_status: str | None = None
    kind: str | None = None
    image_model: str | None = None
    animation_model: str | None = None
    parent_animation_model: str | None = None


class Usage(BaseModel):
    """Response from ``GET /usage`` (OpenAPI ``UsageResponse``)."""

    model_config = ConfigDict(extra="ignore")

    balance_credits: OptionalDecimal = None
    reserved_credits: OptionalDecimal = None
    summary: list[UsageSummary] = []
    records: list[UsageRecord] = []
    next_cursor: str | None = None
    total: int = 0


class UsageHistogramSource(BaseModel):
    """A spend source in a usage histogram (OpenAPI ``UsageHistogramSource``)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    label: str = ""
    kind: str = ""


class HistogramBucket(BaseModel):
    """A single histogram bucket (OpenAPI ``UsageHistogramBucket``)."""

    model_config = ConfigDict(extra="ignore")

    start: datetime
    end: datetime
    total: DecimalValue
    values: DecimalMap = {}


class UsageHistogram(BaseModel):
    """Response from ``GET /usage/histogram`` (OpenAPI ``UsageHistogram``)."""

    model_config = ConfigDict(extra="ignore")

    range: str
    width_seconds: int
    sources: list[UsageHistogramSource] = []
    buckets: list[HistogramBucket] = []
