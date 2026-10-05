"""Exports an animation run in every supported format, writing the results to
``./gametorch-exports/``.

This example is read-only and does **not** spend credits, but the run it exports
must already exist. Set ``GAMETORCH_RUN`` to a run UUID, or it will pick the
first run with frames it can find.

Run with::

    GAMETORCH_API_KEY=gt2_... GAMETORCH_BASE_URL=http://localhost:8300/api \
        python examples/export_animation.py
"""

import json
import os
from pathlib import Path
from uuid import UUID

from gametorch import Client, Export, ExportFormat, ListParams

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

FILENAMES = {
    ExportFormat.TEXTURE_PACKER: "texturepacker.json",
    ExportFormat.TEXTURE_PACKER_ZIP: "texturepacker.zip",
    ExportFormat.ASEPRITE: "animation.aseprite",
    ExportFormat.GODOT: "godot.json",
    ExportFormat.GODOT_ZIP: "godot.zip",
    ExportFormat.GRID: "grid.png",
    ExportFormat.GAME_MAKER: "gamemaker.png",
    ExportFormat.SEQUENCE_ZIP: "sequence.zip",
}


def main() -> None:
    out_dir = Path("gametorch-exports")
    out_dir.mkdir(exist_ok=True)

    with Client.from_env() as client:
        run_id, last_frame = resolve_run(client)
        end = min(last_frame, 3)
        print(f"exporting run {run_id}, frames 1-{end} to {out_dir}")

        for format in ALL_FORMATS:
            export = client.export(run_id, format, 1, end)
            write_export(out_dir / FILENAMES[format], format, export)


def resolve_run(client: Client) -> tuple[UUID, int]:
    if os.environ.get("GAMETORCH_RUN"):
        run_id = UUID(os.environ["GAMETORCH_RUN"])
        run = client.get_animation_run(run_id)
        last = run.frames[-1].frame_number if run.frames else 1
        return run_id, last

    for project in client.list_projects().projects:
        for run in client.list_animation_runs(
            project.id, ListParams(include_archived=True)
        ).animations:
            if run.frames:
                return run.id, run.frames[-1].frame_number
    raise SystemExit("no animation run with frames found; set GAMETORCH_RUN to a run UUID")


def write_export(path: Path, format: ExportFormat, export: Export) -> None:
    if export.binary is not None:
        path.write_bytes(export.binary.data)
        print(f"  {format:<18} -> {path} ({export.binary.len()} bytes)")
    elif export.texturepacker is not None:
        path.write_text(json.dumps(export.texturepacker.model_dump(), indent=2))
        print(f"  {format:<18} -> {path}")
    elif export.godot is not None:
        path.write_text(json.dumps(export.godot.model_dump(), indent=2))
        print(f"  {format:<18} -> {path}")


if __name__ == "__main__":
    main()
