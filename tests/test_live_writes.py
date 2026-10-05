"""Opt-in live write tests that do **not** spend credits.

Enabled only when both ``GAMETORCH_API_KEY`` and ``GAMETORCH_LIVE_WRITES=1`` are
set. Each test creates its own project and deletes it again at the end, unless
``GAMETORCH_KEEP_PROJECT=1`` is set.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from gametorch import (
    ApiError,
    ApiKeyScope,
    AsyncClient,
    CreateApiKeyRequest,
    SpendResetCadence,
    UpdateApiKeyRequest,
)
from tests.support import (
    create_project_or_none,
    finish_project,
    project_name,
    short_name,
)

pytestmark = pytest.mark.live_writes


async def test_project_lifecycle(writes_client: AsyncClient) -> None:
    project = await create_project_or_none(writes_client, "Project Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    projects = await writes_client.list_projects()
    assert any(p.id == project.id for p in projects.projects)

    renamed = await writes_client.rename_project(project.slug, project_name("Renamed"))
    assert renamed.id == project.id

    await finish_project(writes_client, renamed.slug)


async def test_label_lifecycle(writes_client: AsyncClient) -> None:
    project = await create_project_or_none(writes_client, "Label Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    name = short_name("sdk-label")
    label = await writes_client.create_label(project.id, name, "#123456")
    assert label.name == name

    new_name = short_name("sdk-renamed")
    updated = await writes_client.update_label(label.id, name=new_name, color="#654321")
    assert updated.name == new_name

    labels = await writes_client.list_labels(project.id)
    assert any(item.id == label.id for item in labels.labels)

    await writes_client.delete_label(label.id)

    kept = await writes_client.create_label(project.id, short_name("sdk-kept"), "#8bc34a")
    print(f"kept label '{kept.name}'")

    await finish_project(writes_client, project.slug)


async def test_art_style_lifecycle(writes_client: AsyncClient) -> None:
    project = await create_project_or_none(writes_client, "Art Style Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    name = short_name("sdk-style")
    style = await writes_client.create_art_style(project.id, name)
    assert style.name == name

    styles = await writes_client.list_art_styles(project.id)
    assert any(item.id == style.id for item in styles.art_styles)

    await writes_client.delete_art_style(style.id)

    kept = await writes_client.create_art_style(project.id, short_name("sdk-kept-style"))
    print(f"kept art style '{kept.name}'")

    await finish_project(writes_client, project.slug)


async def test_generate_art_style_decodes(writes_client: AsyncClient) -> None:
    project = await create_project_or_none(writes_client, "Art Style Suggest Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    suggestion = await writes_client.generate_art_style(project.id)
    assert suggestion.name

    await finish_project(writes_client, project.slug)


async def test_ensure_user_ok(writes_client: AsyncClient) -> None:
    response = await writes_client.ensure_user()
    assert response.ok


async def test_key_lifecycle(writes_client: AsyncClient) -> None:
    try:
        created = await writes_client.create_key(
            CreateApiKeyRequest.new().name(short_name("sdk-key"))
        )
    except ApiError as err:
        if err.is_forbidden():
            pytest.skip("this key cannot manage API keys (admin required)")
        raise

    assert created.key_full
    assert created.key.key_prefix

    updated = await writes_client.update_key(
        created.key.id, UpdateApiKeyRequest.new().name(short_name("sdk-key-renamed"))
    )
    assert updated.name is not None

    await writes_client.delete_key(created.key.id)


async def test_scoped_key_lifecycle(writes_client: AsyncClient) -> None:
    project = await create_project_or_none(writes_client, "Scoped Key Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    expires_at = datetime.now(UTC) + timedelta(days=30)
    try:
        read = await writes_client.create_key(
            CreateApiKeyRequest.project_read(project.id)
            .name(short_name("sdk-read"))
            .max_spend_limit(Decimal(0))
            .spend_reset_cadence(SpendResetCadence.MONTHLY)
            .expires_at(expires_at)
        )
    except ApiError as err:
        if err.is_forbidden():
            pytest.skip("this key cannot manage API keys (admin required)")
        raise

    assert read.key.key_scope is ApiKeyScope.PROJECT_READ
    assert read.key.project_id == project.id
    assert read.key.name is not None
    assert read.key.expires_at is not None

    write = await writes_client.create_key(
        CreateApiKeyRequest.project_write(project.id)
        .name(short_name("sdk-write"))
        .max_spend_limit(Decimal(500))
        .spend_reset_cadence(SpendResetCadence.WEEKLY)
        .expires_at(expires_at)
    )
    assert write.key.key_scope is ApiKeyScope.PROJECT_WRITE
    assert write.key.project_id == project.id
    assert write.key.max_spend_limit == Decimal(500)

    updated = await writes_client.update_key(
        write.key.id,
        UpdateApiKeyRequest.new()
        .name(short_name("sdk-write-renamed"))
        .max_spend_limit(Decimal(750))
        .spend_reset_cadence(SpendResetCadence.MONTHLY)
        .expires_at(expires_at + timedelta(days=30)),
    )
    assert updated.max_spend_limit == Decimal(750)
    assert updated.spend_reset_cadence == "monthly"

    await writes_client.delete_key(read.key.id)
    await writes_client.delete_key(write.key.id)

    await finish_project(writes_client, project.slug)
