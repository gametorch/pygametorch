"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from gametorch import AsyncClient
from tests.support import (
    has_api_key,
    live_params,
    live_spend_enabled,
    live_writes_enabled,
)


@pytest.fixture
async def live_client():
    """An authenticated async client, or skip when no API key is configured."""
    if not has_api_key():
        pytest.skip("skipping live test: GAMETORCH_API_KEY is not set")
    async with AsyncClient(**live_params()) as client:
        yield client


@pytest.fixture
async def writes_client():
    """A live client for opt-in write tests (``GAMETORCH_LIVE_WRITES=1``)."""
    if not has_api_key() or not live_writes_enabled():
        pytest.skip("skipping: set GAMETORCH_LIVE_WRITES=1 and GAMETORCH_API_KEY")
    async with AsyncClient(**live_params()) as client:
        yield client


@pytest.fixture
async def spend_client():
    """A live client for opt-in spend tests (``GAMETORCH_LIVE_SPEND=1``)."""
    if not has_api_key() or not live_spend_enabled():
        pytest.skip("skipping: set GAMETORCH_LIVE_SPEND=1 and GAMETORCH_API_KEY")
    async with AsyncClient(**live_params()) as client:
        yield client


@pytest.fixture
async def anonymous_client():
    """An unauthenticated async client pointed at the configured deployment."""
    import os

    from gametorch import ENV_BASE_URL

    base_url = os.environ.get(ENV_BASE_URL)
    kwargs = {"base_url": base_url} if base_url else {}
    async with AsyncClient(**kwargs) as client:
        yield client
