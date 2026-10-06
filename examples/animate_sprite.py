"""Creates a new project, generates a sprite, then generates an animation that
uses that sprite as its reference image (``base_asset_id``) so the animation
stays on-model with the sprite.

**This example spends credits** (one sprite and one animation). It creates a
fresh project and deletes it again at the end. Set ``GAMETORCH_KEEP_PROJECT=1``
to keep the project so you can inspect it in the GameTorch UI.

Run with::

    GAMETORCH_API_KEY=gt2_... python examples/animate_sprite.py
"""

import os
import time
from uuid import uuid4

from gametorch import Client, Project, SpriteMode


def project_name(kind: str) -> str:
    return f"SDK {kind} {uuid4().hex[:8]}"


def main() -> None:
    with Client.from_env() as client:
        project = client.create_project(project_name("Reference Animation"))
        print(f"created project '{project.name}' ({project.slug})")
        try:
            run(client, project)
        finally:
            if os.environ.get("GAMETORCH_KEEP_PROJECT") == "1":
                print(f"keeping project '{project.slug}' (GAMETORCH_KEEP_PROJECT=1)")
            else:
                client.delete_project(project.slug)
                print(f"deleted project '{project.slug}'")


def wait_for_generation(client: Client, generation_id):
    while True:
        generation = client.get_generation(generation_id, include_archived=True)
        print(f"sprite status: {generation.status}")
        if generation.status not in ("queued", "running"):
            return generation
        time.sleep(2)


def wait_for_animation(client: Client, run_id):
    while True:
        run = client.get_animation_run(run_id)
        print(f"animation status: {run.status}")
        if run.status not in ("queued", "running"):
            return run
        time.sleep(3)


def run(client: Client, project: Project) -> None:
    # 1. Generate the sprite the animation should stay on-model with.
    models = client.sprite_models()
    image_model = next(model.id for model in models.image_models if model.available)
    sprite_job = (
        client.generate_sprite(project.id)
        .prompt("a friendly red fox, side view, game sprite")
        .mode(SpriteMode.SINGLE)
        .image_model(image_model)
        .send()
    )
    print(f"sprite generation {sprite_job.id} is {sprite_job.status}")

    generation = wait_for_generation(client, sprite_job.id)
    if not generation.assets:
        print(f"sprite generation produced no assets (status: {generation.status})")
        return

    sprite_asset = generation.assets[0]
    print(f"sprite asset {sprite_asset.id} ({sprite_asset.width}x{sprite_asset.height})")

    # 2. Animate that sprite by passing its asset id as the reference image.
    #    Omit .base_asset_id(...) to generate an animation from scratch instead.
    animation_job = (
        client.generate_animation(project.id)
        .prompt("the fox looks around, tail swishing")
        .animation_model("ash")
        .duration(4)
        .base_asset_id(sprite_asset.id)
        .send()
    )
    print(f"animation {animation_job.id} is {animation_job.status}")

    animation = wait_for_animation(client, animation_job.id)
    print(f"animation status: {animation.status}, base_asset_id: {animation.base_asset_id}")


if __name__ == "__main__":
    main()
