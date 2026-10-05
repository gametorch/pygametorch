"""Creates a new project, generates a single sprite in it, then names the
sprite, tags it with metadata and a label, and cleans those annotations up
again.

**This example spends credits.** It creates a fresh project and deletes it again
at the end. Set ``GAMETORCH_KEEP_PROJECT=1`` to keep the project so you can
inspect it in the GameTorch UI.

Run with::

    GAMETORCH_API_KEY=gt2_... python examples/generate_sprite.py
"""

import os
import time
from uuid import uuid4

from gametorch import Client, Project, SpriteMode

FILEPATH = "/foo/bar/sprites/hero.png"


def project_name(kind: str) -> str:
    return f"SDK {kind} {uuid4().hex[:8]}"


def main() -> None:
    with Client.from_env() as client:
        project = client.create_project(project_name("Sprite Example"))
        print(f"created project '{project.name}' ({project.slug})")
        try:
            run(client, project)
        finally:
            if os.environ.get("GAMETORCH_KEEP_PROJECT") == "1":
                print(f"keeping project '{project.slug}' (GAMETORCH_KEEP_PROJECT=1)")
            else:
                client.delete_project(project.slug)
                print(f"deleted project '{project.slug}'")


def run(client: Client, project: Project) -> None:
    models = client.sprite_models()
    image_model = next(model.id for model in models.image_models if model.available)

    job = (
        client.generate_sprite(project.id)
        .prompt("a friendly red fox, side view, game sprite")
        .mode(SpriteMode.SINGLE)
        .image_model(image_model)
        .send()
    )
    print(f"generation {job.id} is {job.status}")

    while True:
        generation = client.get_generation(job.id, include_archived=True)
        print(f"status: {generation.status}")
        if generation.status not in ("queued", "running"):
            break
        time.sleep(2)

    if not generation.assets:
        print(f"generation produced no assets (status: {generation.status})")
        return

    asset = generation.assets[0]
    print(f"asset {asset.id} ({asset.width}x{asset.height})")

    named = client.rename_asset(asset.id, "Hero Fox")
    print(f"named asset: {named.name}")

    updated = client.put_asset_metadata(asset.id, {"filepath": FILEPATH})
    print(f"metadata after add: {updated.metadata}")
    cleared = client.put_asset_metadata(asset.id, {})
    print(f"metadata after remove: {cleared.metadata}")
    client.put_asset_metadata(asset.id, {"filepath": FILEPATH})

    label = client.create_label(project.id, f"sprite-{uuid4().hex[:8]}", "#4caf50")
    associated = client.associate_asset_label(asset.id, label.name)
    print(f"labels after add: {associated.labels}")
    removed = client.remove_asset_label(asset.id, label.name)
    print(f"labels after remove: {removed.labels}")
    client.associate_asset_label(asset.id, label.name)
    print(f"kept label {label.name!r}")

    png = client.asset_content(asset.id)
    print(f"downloaded {png.len()} bytes of {png.content_type}")


if __name__ == "__main__":
    main()
