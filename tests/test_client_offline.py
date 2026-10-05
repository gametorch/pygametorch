"""Offline tests for request construction, retries, builders and pagination.

These use ``httpx.MockTransport`` so they never touch the network.
"""

from __future__ import annotations

import json
from datetime import UTC
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest

from gametorch import (
    ApiError,
    AsyncClient,
    Client,
    ConfigError,
    CreateApiKeyRequest,
    ExportFormat,
    ListParams,
    RateLimitedError,
    SpriteMode,
)
from gametorch._api.sprites import SpriteGenerationBuilder

PROJECT_ID = UUID("afb90af1-80a4-4c75-9328-2de4edde4b16")
GENERATION_ID = UUID("b58cc74c-ea81-4a9b-b418-d785192011a4")


def generation_json(generation_id: UUID, *, next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "generations": [generation_object(generation_id)],
        "next_cursor": next_cursor,
        "total": 1,
    }


def generation_object(generation_id: UUID) -> dict[str, Any]:
    return {
        "id": str(generation_id),
        "project_id": str(PROJECT_ID),
        "prompt": "a red fox",
        "mode": "single",
        "image_model": "openai/gpt-image-2.5-flare",
        "status": "succeeded",
        "credits_consumed": "5.0",
        "reserved_credits": "0.0",
        "assets_delivered": 1,
        "created_at": "2026-10-01T21:10:48.237007+00:00",
        "assets": [],
    }


def client_with(handler: Any, **kwargs: Any) -> AsyncClient:
    transport = httpx.MockTransport(handler)
    return AsyncClient(
        api_key="gt2_test",
        base_url="http://test.local/api",
        transport=transport,
        retry_base_delay=0.0,
        **kwargs,
    )


async def test_authorization_and_accept_headers() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        seen["accept"] = request.headers.get("accept")
        seen["user_agent"] = request.headers.get("user-agent")
        return httpx.Response(200, json={"projects": []})

    async with client_with(handler) as client:
        await client.list_projects()

    assert seen["auth"] == "Bearer gt2_test"
    assert seen["accept"] == "application/json"
    assert seen["user_agent"].startswith("gametorch-python/")


async def test_base_url_and_path() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"projects": []})

    async with client_with(handler) as client:
        await client.list_projects()

    assert seen["url"] == "http://test.local/api/projects"


async def test_include_archived_query() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=generation_object(GENERATION_ID))

    async with client_with(handler) as client:
        await client.get_generation(GENERATION_ID, include_archived=True)

    assert seen["params"]["include_archived"] == "true"


async def test_base_asset_filter_query() -> None:
    seen: dict[str, Any] = {}
    base = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        seen["params"] = dict(request.url.params)
        return httpx.Response(
            200,
            json={"animations": [], "next_cursor": None, "total": 0},
        )

    async with client_with(handler) as client:
        await client.list_animation_runs(
            PROJECT_ID, ListParams(include_archived=True, base_asset_id=base)
        )

    assert seen["params"]["include_archived"] == "true"
    assert seen["params"]["base_asset_id"] == str(base)


async def test_retries_on_server_error_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, json={"projects": []})

    async with client_with(handler, max_retries=3) as client:
        await client.list_projects()

    assert calls["n"] == 3


async def test_retries_honor_retry_after() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "0"}, text="slow")
        return httpx.Response(200, json={"projects": []})

    async with client_with(handler, max_retries=1) as client:
        await client.list_projects()

    assert calls["n"] == 2


async def test_rate_limited_after_exhausting_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    async with client_with(handler, max_retries=1) as client:
        with pytest.raises(RateLimitedError) as excinfo:
            await client.list_projects()
    assert excinfo.value.attempts == 2


async def test_api_error_on_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "no such project"})

    async with client_with(handler) as client:
        with pytest.raises(ApiError) as excinfo:
            await client.list_projects()
    assert excinfo.value.status == 404
    assert excinfo.value.message == "no such project"
    assert excinfo.value.is_not_found()


async def test_download_returns_bytes_and_content_type() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"PNGDATA", headers={"content-type": "image/png"})

    async with client_with(handler) as client:
        download = await client.asset_content(uuid4())
    assert download.data == b"PNGDATA"
    assert download.content_type == "image/png"
    assert download.len() == 7
    assert not download.is_empty()


async def test_health_returns_trimmed_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok\n")

    async with client_with(handler) as client:
        assert await client.health() == "ok"


async def test_sprite_builder_body_and_request_id() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": str(GENERATION_ID),
                "status": "queued",
                "created": True,
                "reserved_credits": "5.0",
            },
        )

    request_id = uuid4()
    async with client_with(handler) as client:
        job = await (
            client.generate_sprite(PROJECT_ID)
            .prompt("a red fox")
            .mode(SpriteMode.MULTIPLE)
            .image_model("openai/gpt-image-2.5-flare")
            .quality("high")
            .resolution("1K")
            .request_id(request_id)
            .send()
        )

    assert job.status == "queued"
    assert seen["url"].endswith(f"/projects/{PROJECT_ID}/generations")
    assert seen["body"]["request_id"] == str(request_id)
    assert seen["body"]["mode"] == "multiple"
    assert seen["body"]["quality"] == "high"
    assert "text_model" not in seen["body"]


async def test_sprite_builder_requires_prompt_and_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("should not send")

    async with client_with(handler) as client:
        builder = client.generate_sprite(PROJECT_ID)
        with pytest.raises(ConfigError):
            await builder.send()

        builder = client.generate_sprite(PROJECT_ID).prompt("x")
        with pytest.raises(ConfigError):
            await builder.send()


async def test_rename_sends_null_name() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "name": None})

    async with client_with(handler) as client:
        response = await client.rename_asset(uuid4(), None)
    assert seen["body"] == {"name": None}
    assert response.name is None


async def test_metadata_body() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "metadata": seen["body"]["metadata"]})

    async with client_with(handler) as client:
        response = await client.put_asset_metadata(uuid4(), {"filepath": "/a/b.png"})
    assert seen["body"] == {"metadata": {"filepath": "/a/b.png"}}
    assert response.metadata == {"filepath": "/a/b.png"}


async def test_create_key_body_serialization() -> None:
    from datetime import datetime

    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": str(uuid4()),
                "key_prefix": "gt2_abc",
                "spend_reset_cadence": "monthly",
                "key_scope": "project_read",
                "project_id": str(PROJECT_ID),
                "spend": "0",
                "lifetime_spend": "0",
                "created_at": "2026-10-05T00:00:00Z",
                "key_full": "gt2_secret",
            },
        )

    request = (
        CreateApiKeyRequest.project_read(PROJECT_ID)
        .name("CI read key")
        .max_spend_limit(Decimal(0))
        .expires_at(datetime(2026, 12, 31, tzinfo=UTC))
    )
    async with client_with(handler) as client:
        created = await client.create_key(request)

    assert seen["body"]["key_scope"] == "project_read"
    assert seen["body"]["project_id"] == str(PROJECT_ID)
    assert seen["body"]["max_spend_limit"] == "0"
    assert seen["body"]["expires_at"].startswith("2026-12-31")
    assert created.key_full == "gt2_secret"
    assert created.key.id is not None


async def test_export_dispatches_by_format() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/export/grid"):
            return httpx.Response(200, content=b"GRID", headers={"content-type": "image/png"})
        return httpx.Response(
            200,
            json={
                "plan": export_plan_json(),
                "tres": "resource",
                "image_base64": "AAA",
                "image_filename": "a.png",
                "tres_filename": "a.tres",
            },
        )

    async with client_with(handler) as client:
        binary = await client.export(GENERATION_ID, ExportFormat.GRID, 1, 3)
        assert binary.is_binary()
        assert binary.binary is not None
        assert binary.binary.data == b"GRID"

        godot = await client.export(GENERATION_ID, ExportFormat.GODOT, 1, 3)
        assert godot.godot is not None
        assert godot.godot.tres == "resource"


def export_plan_json() -> dict[str, Any]:
    return {
        "start_frame": 1,
        "end_frame": 3,
        "frames": [],
        "max_width": 1,
        "max_height": 1,
        "scale": 1.0,
        "scale_width": 1.0,
        "scale_height": 1.0,
        "canvas_width": 1,
        "canvas_height": 1,
        "frame_count": 3,
    }


async def test_paginator_walks_pages() -> None:
    pages: dict[str | None, dict[str, Any]] = {
        None: generation_json(uuid4(), next_cursor="page2"),
        "page2": generation_json(uuid4(), next_cursor=None),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("before")
        return httpx.Response(200, json=pages[cursor])

    async with client_with(handler) as client:
        stream = client.stream_generations(PROJECT_ID)
        ids = [generation.id async for generation in stream]
        assert len(ids) == 2
        assert stream.total == 1


async def test_sync_client_and_paginator() -> None:
    pages: dict[str | None, dict[str, Any]] = {
        None: generation_json(uuid4(), next_cursor="page2"),
        "page2": generation_json(uuid4(), next_cursor=None),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/projects"):
            return httpx.Response(200, json={"projects": []})
        cursor = request.url.params.get("before")
        return httpx.Response(200, json=pages[cursor])

    transport = httpx.MockTransport(handler)
    with Client(
        api_key="gt2_test",
        base_url="http://test.local/api",
        transport=transport,
        retry_base_delay=0.0,
    ) as client:
        assert client.list_projects().projects == []
        stream = client.stream_generations(PROJECT_ID)
        ids = [generation.id for generation in stream]
        assert len(ids) == 2


async def test_sync_builder_runs_synchronously() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": str(GENERATION_ID),
                "status": "queued",
                "created": True,
                "reserved_credits": "5.0",
            },
        )

    transport = httpx.MockTransport(handler)
    with Client(
        api_key="gt2_test",
        base_url="http://test.local/api",
        transport=transport,
        retry_base_delay=0.0,
    ) as client:
        job = (
            client.generate_sprite(PROJECT_ID)
            .prompt("a red fox")
            .image_model("openai/gpt-image-2.5-flare")
            .send()
        )
    assert job.status == "queued"


async def test_sync_client_is_not_async_client() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"projects": []}))
    with Client(api_key="k", transport=transport) as client:
        assert not isinstance(client, AsyncClient)
        assert client.is_authenticated


async def test_builder_is_not_dispatched_until_send() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("should not send")

    async with client_with(handler) as client:
        builder = client.generate_sprite(PROJECT_ID)
        assert isinstance(builder, SpriteGenerationBuilder)
