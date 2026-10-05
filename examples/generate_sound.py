"""Creates a new project, generates a sound effect in it, then names the sound,
tags it with metadata and a label, and cleans those annotations up again.

**This example spends credits.** It creates a fresh project and deletes it again
at the end. Set ``GAMETORCH_KEEP_PROJECT=1`` to keep the project.

Run with::

    GAMETORCH_API_KEY=gt2_... python examples/generate_sound.py
"""

import os
import time
from uuid import uuid4

from gametorch import Client, Project

FILEPATH = "/foo/bar/audio/sword-unsheath.mp3"


def project_name(kind: str) -> str:
    return f"SDK {kind} {uuid4().hex[:8]}"


def main() -> None:
    with Client.from_env() as client:
        project = client.create_project(project_name("Sound Example"))
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
    models = client.sound_models()
    job = (
        client.generate_sound(project.id)
        .prompt("a single sword unsheathing, then a heavy metal thud")
        .sound_model(models.model.id)
        .response_format(models.default_format)
        .send()
    )
    print(f"sound generation {job.id} is {job.status}")

    while True:
        generation = client.get_sound_generation(job.id, include_archived=True)
        print(f"status: {generation.status}")
        if generation.status not in ("queued", "running"):
            break
        time.sleep(2)

    if not generation.assets:
        print(f"generation produced no assets (status: {generation.status})")
        return

    asset = generation.assets[0]
    print(f"asset {asset.id} ({asset.format})")

    named = client.rename_sound_asset(asset.id, "Sword Unsheath")
    print(f"named sound: {named.name}")

    updated = client.put_sound_asset_metadata(asset.id, {"filepath": FILEPATH})
    print(f"metadata after add: {updated.metadata}")
    cleared = client.put_sound_asset_metadata(asset.id, {})
    print(f"metadata after remove: {cleared.metadata}")
    client.put_sound_asset_metadata(asset.id, {"filepath": FILEPATH})

    label = client.create_label(project.id, f"sound-{uuid4().hex[:8]}", "#2196f3")
    associated = client.associate_sound_label(asset.id, label.name)
    print(f"labels after add: {associated.labels}")
    removed = client.remove_sound_label(asset.id, label.name)
    print(f"labels after remove: {removed.labels}")
    client.associate_sound_label(asset.id, label.name)
    print(f"kept label {label.name!r}")

    audio = client.sound_asset_content(asset.id)
    print(f"downloaded {audio.len()} bytes of {audio.content_type}")


if __name__ == "__main__":
    main()
