"""Creates a new project, generates an animation in it, generates its frames,
saves a sub-range as a named preset with metadata and a label, then exports it
in every supported format.

**This example spends credits** (animation generation and, if needed, frame
generation). It creates a fresh project and deletes it again at the end. Set
``GAMETORCH_KEEP_PROJECT=1`` to keep the project.

Run with::

    GAMETORCH_API_KEY=gt2_... python examples/generate_animation.py
"""

import os
import time
from uuid import uuid4

from gametorch import Client, Export, ExportFormat, Project

FILEPATH = "/foo/bar/animations/sword-raise.aseprite"

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


def project_name(kind: str) -> str:
    return f"SDK {kind} {uuid4().hex[:8]}"


def main() -> None:
    with Client.from_env() as client:
        project = client.create_project(project_name("Animation Example"))
        print(f"created project '{project.name}' ({project.slug})")
        try:
            run(client, project)
        finally:
            if os.environ.get("GAMETORCH_KEEP_PROJECT") == "1":
                print(f"keeping project '{project.slug}' (GAMETORCH_KEEP_PROJECT=1)")
            else:
                client.delete_project(project.slug)
                print(f"deleted project '{project.slug}'")


def wait_for_animation(client: Client, run_id):
    while True:
        run = client.get_animation_run(run_id)
        print(f"status: {run.status}")
        if run.status not in ("queued", "running"):
            return run
        time.sleep(3)


def wait_for_frames(client: Client, run_id):
    last_len = 0
    for _ in range(180):
        run = client.get_animation_run(run_id)
        settled = all(fr.status not in ("queued", "running") for fr in run.frame_runs)
        if run.frames and settled and len(run.frames) == last_len:
            return run
        last_len = len(run.frames)
        time.sleep(2)
    return client.get_animation_run(run_id)


def run(client: Client, project: Project) -> None:
    job = (
        client.generate_animation(project.id)
        .prompt("the hero draws her sword and raises it overhead")
        .animation_model("ash")
        .duration(4)
        .send()
    )
    print(f"animation {job.id} is {job.status}")

    run_ = wait_for_animation(client, job.id)
    if not run_.frames:
        client.generate_frames(project.id, run_.id).fps(12).send()
    run_ = wait_for_frames(client, run_.id)

    if not run_.frames:
        print("no frames available; skipping saved animation and exports")
        return

    last = run_.frames[-1].frame_number
    start_frame = min(2, last)
    end_frame = max(last - 1, start_frame)
    saved = (
        client.save_animation(project.id)
        .generation_id(run_.id)
        .range(start_frame, end_frame)
        .name("Sword Raise")
        .send()
    )
    print(
        f"saved animation {saved.id} ({saved.frame_count} frames, "
        f"{saved.start_frame}-{saved.end_frame})"
    )

    renamed = client.rename_saved_animation(saved.id, "Sword Raise (named)")
    print(f"renamed saved animation: {renamed.name}")

    tagged = client.put_saved_animation_metadata(saved.id, {"filepath": FILEPATH})
    print(f"metadata after add: {tagged.metadata}")
    client.put_saved_animation_metadata(saved.id, {})
    client.put_saved_animation_metadata(saved.id, {"filepath": FILEPATH})

    label = client.create_label(project.id, f"anim-{uuid4().hex[:8]}", "#ff9800")
    associated = client.associate_saved_animation_label(saved.id, label.name)
    print(f"labels after add: {associated.labels}")
    removed = client.remove_saved_animation_label(saved.id, label.name)
    print(f"labels after remove: {removed.labels}")
    client.associate_saved_animation_label(saved.id, label.name)
    print(f"kept label {label.name!r}")

    frame = client.frame_content_by_number(run_.id, start_frame)
    print(f"frame {start_frame}: {frame.len()} bytes")

    print(f"\nexports ({start_frame}-{end_frame}):")
    for format in ALL_FORMATS:
        export = client.export(run_.id, format, start_frame, end_frame)
        describe_export(format, export)


def describe_export(format: ExportFormat, export: Export) -> None:
    if export.binary is not None:
        print(f"  {format:<18} {export.binary.len()} bytes ({export.binary.content_type or '?'})")
    elif export.texturepacker is not None:
        print(
            f"  {format:<18} json, image {len(export.texturepacker.image_base64)} bytes, "
            f"atlas {export.texturepacker.json_filename}"
        )
    elif export.godot is not None:
        print(
            f"  {format:<18} json, image {len(export.godot.image_base64)} bytes, "
            f"resource {export.godot.tres_filename}"
        )


if __name__ == "__main__":
    main()
