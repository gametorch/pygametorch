"""Live read-only integration tests.

These run only when ``GAMETORCH_API_KEY`` is set, so ``pytest`` stays offline by
default. Point them at a local deployment with
``GAMETORCH_BASE_URL=http://localhost:8300/api``.

They exercise read-only endpoints (and the read-only export plan), so they never
spend credits.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from gametorch import ApiError, AsyncClient, ListParams
from tests.support import has_api_key

pytestmark = pytest.mark.live


async def first_project(client: AsyncClient) -> UUID | None:
    projects = await client.list_projects()
    return projects.projects[0].id if projects.projects else None


async def test_health_is_ok(live_client: AsyncClient) -> None:
    status = await live_client.health()
    assert status


async def test_catalogs_decode(live_client: AsyncClient) -> None:
    sprites = await live_client.sprite_models()
    assert sprites.image_models

    sounds = await live_client.sound_models()
    assert sounds.formats

    animations = await live_client.animation_models()
    assert animations.data


async def test_list_projects_decodes(live_client: AsyncClient) -> None:
    projects = await live_client.list_projects()
    for project in projects.projects:
        assert project.slug


async def test_usage_decodes(live_client: AsyncClient) -> None:
    usage = await live_client.usage()
    assert usage.total >= 0

    histogram = await live_client.usage_histogram("24h")
    assert histogram.range == "24h"


async def test_generations_and_assets_decode(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    params = ListParams(include_archived=True)
    generations = await live_client.list_generations(project_id, params)

    for generation in generations.generations[:3]:
        fetched = await live_client.get_generation(generation.id, include_archived=True)
        assert fetched.id == generation.id

        if fetched.assets:
            asset = await live_client.get_asset(fetched.assets[0].id)
            assert asset.id == fetched.assets[0].id
            content = await live_client.asset_content(asset.id)
            assert not content.is_empty()
            if asset.has_original:
                original = await live_client.asset_original(asset.id)
                assert not original.is_empty()

    assets = await live_client.list_sprite_assets(project_id)
    for asset in assets.assets[:3]:
        assert asset.width >= 0


async def test_sounds_decode(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    sounds = await live_client.list_sound_generations(project_id, ListParams(include_archived=True))
    for generation in sounds.sound_generations[:3]:
        fetched = await live_client.get_sound_generation(generation.id, include_archived=True)
        assert fetched.id == generation.id
        if fetched.assets:
            content = await live_client.sound_asset_content(fetched.assets[0].id)
            assert not content.is_empty()


async def test_animations_and_exports_decode(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    runs = await live_client.list_animation_runs(project_id, ListParams(include_archived=True))
    for run in runs.animations[:2]:
        fetched = await live_client.get_animation_run(run.id)
        assert fetched.id == run.id
        assert fetched.provenance.source

        if fetched.frames:
            frame = fetched.frames[0]
            content = await live_client.frame_content(frame.id)
            assert not content.is_empty()
            plan = await live_client.export_plan(run.id, 1, 2)
            assert plan.frame_count >= 0

    base = next((run.base_asset_id for run in runs.animations if run.base_asset_id), uuid4())
    filtered = await live_client.list_animation_runs(
        project_id, ListParams(include_archived=True, base_asset_id=base)
    )
    assert all(run.base_asset_id == base for run in filtered.animations)


async def test_saved_animations_decode(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    saved = await live_client.list_saved_animations(project_id, ListParams(include_archived=True))
    for animation in saved.saved_animations[:3]:
        fetched = await live_client.get_saved_animation(animation.id)
        assert fetched.id == animation.id


async def test_labels_and_art_styles_decode(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    labels = await live_client.list_labels(project_id)
    if labels.labels:
        items = await live_client.label_items(labels.labels[0].id)
        assert items.label.id == labels.labels[0].id

    styles = await live_client.list_art_styles(project_id)
    for style in styles.art_styles:
        assert style.name


async def test_keys_decode_or_forbidden(live_client: AsyncClient) -> None:
    try:
        keys = await live_client.list_keys()
    except ApiError as err:
        if err.is_forbidden():
            return
        raise
    for key in keys.keys:
        assert key.key_prefix


async def test_animation_estimate_decodes(live_client: AsyncClient) -> None:
    project_id = await first_project(live_client)
    if project_id is None:
        pytest.skip("no projects")

    estimate = await (
        live_client.estimate_animation(project_id).animation_model("ash").duration(4).send()
    )
    assert estimate.animation_model == "ash"
    assert estimate.duration == 4
    assert estimate.resolution


async def test_unauthenticated_requests_are_rejected(
    anonymous_client: AsyncClient,
) -> None:
    if not has_api_key():
        pytest.skip("skipping live test: GAMETORCH_API_KEY is not set")

    with pytest.raises(ApiError) as excinfo:
        await anonymous_client.list_projects()
    assert excinfo.value.status == 401
