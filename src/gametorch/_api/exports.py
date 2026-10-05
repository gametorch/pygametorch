"""Animation export endpoints."""

from __future__ import annotations

from uuid import UUID

from .._rate_limit import Concurrency, RateClass
from .._types import Download, ExportFormat
from ..models import Export, ExportPlan, GodotExport, TexturePackerExport

IdLike = UUID | str


class ExportsMixin:
    """Animation export endpoints."""

    async def export_plan(self, run_id: IdLike, start_frame: int, end_frame: int) -> ExportPlan:
        """Returns the export plan without building a file.

        ``POST /animation-runs/{id}/export-plan``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            ExportPlan,
            "POST",
            f"animation-runs/{run_id}/export-plan",
            rate_class=RateClass.TIER1,
            route="POST /animation-runs/{id}/export-plan",
            concurrency=Concurrency.NONE,
            json_body={"start_frame": start_frame, "end_frame": end_frame},
        )

    async def export(
        self,
        run_id: IdLike,
        format: ExportFormat,
        start_frame: int,
        end_frame: int,
    ) -> Export:
        """Builds and returns an export in the requested format.

        The result is structured JSON for :attr:`ExportFormat.TEXTURE_PACKER` and
        :attr:`ExportFormat.GODOT`, and raw bytes for every other format.

        ``POST /animation-runs/{id}/export/{format}``
        """
        if format is ExportFormat.TEXTURE_PACKER:
            return Export(
                texturepacker=await self.export_texturepacker(run_id, start_frame, end_frame)
            )
        if format is ExportFormat.GODOT:
            return Export(godot=await self.export_godot(run_id, start_frame, end_frame))
        return Export(binary=await self._export_binary(run_id, format, start_frame, end_frame))

    async def _export_binary(
        self,
        run_id: IdLike,
        format: ExportFormat,
        start_frame: int,
        end_frame: int,
    ) -> Download:
        """Exports a binary format (PNG or zip) and returns the raw bytes."""
        return await self._send_download(  # type: ignore[attr-defined]
            "POST",
            f"animation-runs/{run_id}/export/{format.as_str()}",
            rate_class=RateClass.TIER1,
            route="POST /animation-runs/{id}/export/{format}",
            concurrency=Concurrency.NONE,
            json_body={"start_frame": start_frame, "end_frame": end_frame},
        )

    async def export_texturepacker(
        self, run_id: IdLike, start_frame: int, end_frame: int
    ) -> TexturePackerExport:
        """Exports a TexturePacker JSON atlas (returned as structured JSON)."""
        return await self._send_json(  # type: ignore[attr-defined]
            TexturePackerExport,
            "POST",
            f"animation-runs/{run_id}/export/texturepacker",
            rate_class=RateClass.TIER1,
            route="POST /animation-runs/{id}/export/texturepacker",
            concurrency=Concurrency.NONE,
            json_body={"start_frame": start_frame, "end_frame": end_frame},
        )

    async def export_godot(self, run_id: IdLike, start_frame: int, end_frame: int) -> GodotExport:
        """Exports a Godot ``.tres`` resource and PNG (structured JSON)."""
        return await self._send_json(  # type: ignore[attr-defined]
            GodotExport,
            "POST",
            f"animation-runs/{run_id}/export/godot",
            rate_class=RateClass.TIER1,
            route="POST /animation-runs/{id}/export/godot",
            concurrency=Concurrency.NONE,
            json_body={"start_frame": start_frame, "end_frame": end_frame},
        )

    async def export_texturepacker_zip(
        self, run_id: IdLike, start_frame: int, end_frame: int
    ) -> Download:
        """Exports a zipped TexturePacker JSON atlas."""
        return await self._export_binary(
            run_id, ExportFormat.TEXTURE_PACKER_ZIP, start_frame, end_frame
        )

    async def export_aseprite(self, run_id: IdLike, start_frame: int, end_frame: int) -> Download:
        """Exports an Aseprite file."""
        return await self._export_binary(run_id, ExportFormat.ASEPRITE, start_frame, end_frame)

    async def export_godot_zip(self, run_id: IdLike, start_frame: int, end_frame: int) -> Download:
        """Exports a zipped Godot ``.tres`` and PNG."""
        return await self._export_binary(run_id, ExportFormat.GODOT_ZIP, start_frame, end_frame)

    async def export_grid(self, run_id: IdLike, start_frame: int, end_frame: int) -> Download:
        """Exports a single grid-strip PNG."""
        return await self._export_binary(run_id, ExportFormat.GRID, start_frame, end_frame)

    async def export_gamemaker(self, run_id: IdLike, start_frame: int, end_frame: int) -> Download:
        """Exports a GameMaker strip PNG."""
        return await self._export_binary(run_id, ExportFormat.GAME_MAKER, start_frame, end_frame)

    async def export_sequence_zip(
        self, run_id: IdLike, start_frame: int, end_frame: int
    ) -> Download:
        """Exports a zipped numbered PNG sequence."""
        return await self._export_binary(run_id, ExportFormat.SEQUENCE_ZIP, start_frame, end_frame)


__all__ = ["ExportsMixin"]
