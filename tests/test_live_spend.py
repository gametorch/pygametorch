"""Opt-in live tests that **spend credits**.

These generate real sprites, sounds and animations. Each test creates its own
project and deletes it again at the end, unless ``GAMETORCH_KEEP_PROJECT=1`` is
set.

They only run when ``GAMETORCH_LIVE_SPEND=1`` **and** ``GAMETORCH_API_KEY`` are
set.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import pytest

from gametorch import AsyncClient, Export, ExportFormat, SpriteMode
from gametorch.models import AnimationRun, Generation, SoundGeneration
from tests.support import create_project_or_none, finish_project, short_name

pytestmark = pytest.mark.live_spend

SPRITE_FILEPATH = "/foo/bar/sprites/hero.png"
SOUND_FILEPATH = "/foo/bar/audio/sword-unsheath.mp3"
ANIMATION_FILEPATH = "/foo/bar/animations/sword-raise.aseprite"

ALL_FORMATS = [
    ExportFormat.TEXTURE_PACKER,
    ExportFormat.TEXTURE_PACKER_ZIP,
    ExportFormat.ASEPRITE,
    ExportFormat.GODOT,
    ExportFormat.GODOT_ZIP,
    ExportFormat.GRID,
    ExportFormat.GAME_MAKER,
    ExportFormat.SEQUENCE_ZIP,
]


async def wait_generation(client: AsyncClient, generation_id: UUID) -> Generation:
    for _ in range(120):
        generation = await client.get_generation(generation_id, include_archived=True)
        if generation.status not in ("queued", "running"):
            return generation
        await asyncio.sleep(2)
    raise AssertionError(f"timed out waiting for sprite generation {generation_id}")


async def wait_sound(client: AsyncClient, generation_id: UUID) -> SoundGeneration:
    for _ in range(120):
        generation = await client.get_sound_generation(generation_id, include_archived=True)
        if generation.status not in ("queued", "running"):
            return generation
        await asyncio.sleep(2)
    raise AssertionError(f"timed out waiting for sound generation {generation_id}")


async def wait_animation(client: AsyncClient, run_id: UUID) -> AnimationRun:
    for _ in range(180):
        run = await client.get_animation_run(run_id)
        if run.status not in ("queued", "running"):
            return run
        await asyncio.sleep(3)
    raise AssertionError(f"timed out waiting for animation run {run_id}")


async def wait_for_frames(client: AsyncClient, run_id: UUID) -> AnimationRun:
    last_len = 0
    for _ in range(180):
        run = await client.get_animation_run(run_id)
        settled = all(frame_run.status not in ("queued", "running") for frame_run in run.frame_runs)
        if run.frames and settled and len(run.frames) == last_len:
            return run
        last_len = len(run.frames)
        await asyncio.sleep(2)
    return await client.get_animation_run(run_id)


async def test_sprite_generation_full_flow(spend_client: AsyncClient) -> None:
    project = await create_project_or_none(spend_client, "Sprite Spend Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    models = await spend_client.sprite_models()
    image_model = next(model.id for model in models.image_models if model.available)

    job = await (
        spend_client.generate_sprite(project.id)
        .prompt("a friendly red fox, side view, game sprite")
        .mode(SpriteMode.SINGLE)
        .image_model(image_model)
        .send()
    )

    generation = await wait_generation(spend_client, job.id)
    assert generation.status == "succeeded", f"generation failed: {generation.error}"
    assert generation.assets
    asset = generation.assets[0]

    named = await spend_client.rename_asset(asset.id, "Hero Fox")
    assert named.name == "Hero Fox"

    updated = await spend_client.put_asset_metadata(asset.id, {"filepath": SPRITE_FILEPATH})
    assert updated.metadata.get("filepath") == SPRITE_FILEPATH
    cleared = await spend_client.put_asset_metadata(asset.id, {})
    assert cleared.metadata == {}
    await spend_client.put_asset_metadata(asset.id, {"filepath": SPRITE_FILEPATH})

    label = await spend_client.create_label(project.id, short_name("sprite"))
    associated = await spend_client.associate_asset_label(asset.id, label.name)
    assert label.name in associated.labels
    removed = await spend_client.remove_asset_label(asset.id, label.name)
    assert label.name not in removed.labels
    await spend_client.associate_asset_label(asset.id, label.name)

    archived = await spend_client.archive_asset(asset.id)
    assert archived.archived_at is not None
    unarchived = await spend_client.unarchive_asset(asset.id)
    assert unarchived.archived_at is None

    content = await spend_client.asset_content(asset.id)
    assert not content.is_empty()

    await finish_project(spend_client, project.slug)


async def test_sound_generation_full_flow(spend_client: AsyncClient) -> None:
    project = await create_project_or_none(spend_client, "Sound Spend Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    models = await spend_client.sound_models()
    job = await (
        spend_client.generate_sound(project.id)
        .prompt("a single sword unsheathing, then a heavy metal thud")
        .sound_model(models.model.id)
        .response_format(models.default_format)
        .send()
    )

    generation = await wait_sound(spend_client, job.id)
    assert generation.status == "succeeded", f"generation failed: {generation.error}"
    assert generation.assets
    asset = generation.assets[0]

    named = await spend_client.rename_sound_asset(asset.id, "Sword Unsheath")
    assert named.name == "Sword Unsheath"

    updated = await spend_client.put_sound_asset_metadata(asset.id, {"filepath": SOUND_FILEPATH})
    assert updated.metadata.get("filepath") == SOUND_FILEPATH
    cleared = await spend_client.put_sound_asset_metadata(asset.id, {})
    assert cleared.metadata == {}
    await spend_client.put_sound_asset_metadata(asset.id, {"filepath": SOUND_FILEPATH})

    label = await spend_client.create_label(project.id, short_name("sound"))
    associated = await spend_client.associate_sound_label(asset.id, label.name)
    assert label.name in associated.labels
    removed = await spend_client.remove_sound_label(asset.id, label.name)
    assert label.name not in removed.labels
    await spend_client.associate_sound_label(asset.id, label.name)

    archived = await spend_client.archive_sound_asset(asset.id)
    assert archived.archived_at is not None
    unarchived = await spend_client.unarchive_sound_asset(asset.id)
    assert unarchived.archived_at is None

    content = await spend_client.sound_asset_content(asset.id)
    assert not content.is_empty()

    await finish_project(spend_client, project.slug)


async def test_animation_generation_exports_and_saved_animation(
    spend_client: AsyncClient,
) -> None:
    project = await create_project_or_none(spend_client, "Animation Spend Test")
    if project is None:
        pytest.skip("this key cannot create projects")

    job = await (
        spend_client.generate_animation(project.id)
        .prompt("the hero draws her sword and raises it overhead")
        .animation_model("ash")
        .duration(4)
        .send()
    )

    run = await wait_animation(spend_client, job.id)
    assert run.status == "succeeded", f"animation failed: {run.error}"

    if not run.frames:
        await spend_client.generate_frames(project.id, run.id).fps(12).send()
    run = await wait_for_frames(spend_client, run.id)
    assert run.frames, "animation produced no frames"

    last = run.frames[-1].frame_number
    start_frame = min(2, last)
    end_frame = max(last - 1, start_frame)
    saved = await (
        spend_client.save_animation(project.id)
        .generation_id(run.id)
        .range(start_frame, end_frame)
        .name("Sword Raise")
        .send()
    )
    assert saved.generation_id == run.id
    assert saved.start_frame == start_frame
    assert saved.end_frame == end_frame

    renamed = await spend_client.rename_saved_animation(saved.id, "Sword Raise (named)")
    assert renamed.name == "Sword Raise (named)"

    tagged = await spend_client.put_saved_animation_metadata(
        saved.id, {"filepath": ANIMATION_FILEPATH}
    )
    assert tagged.metadata.get("filepath") == ANIMATION_FILEPATH
    cleared = await spend_client.put_saved_animation_metadata(saved.id, {})
    assert cleared.metadata == {}
    await spend_client.put_saved_animation_metadata(saved.id, {"filepath": ANIMATION_FILEPATH})

    label = await spend_client.create_label(project.id, short_name("anim"))
    associated = await spend_client.associate_saved_animation_label(saved.id, label.name)
    assert label.name in associated.labels
    removed = await spend_client.remove_saved_animation_label(saved.id, label.name)
    assert label.name not in removed.labels
    await spend_client.associate_saved_animation_label(saved.id, label.name)

    archived = await spend_client.archive_saved_animation(saved.id)
    assert archived.archived_at is not None
    unarchived = await spend_client.unarchive_saved_animation(saved.id)
    assert unarchived.archived_at is None

    frame = await spend_client.frame_content_by_number(run.id, start_frame)
    assert not frame.is_empty()

    for format in ALL_FORMATS:
        export = await spend_client.export(run.id, format, start_frame, end_frame)
        if isinstance(export, Export):
            if export.binary is not None:
                assert not export.binary.is_empty(), f"{format} was empty"
            elif export.texturepacker is not None:
                assert export.texturepacker.image_base64
                assert export.texturepacker.json_filename
            elif export.godot is not None:
                assert export.godot.tres
                assert export.godot.image_base64

    await finish_project(spend_client, project.slug)
