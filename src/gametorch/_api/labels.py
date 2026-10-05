"""Label endpoints."""

from __future__ import annotations

from uuid import UUID

from .._rate_limit import Concurrency, RateClass
from .._types import OkResponse
from ..models import Label, LabelAssociation, LabelItems, LabelsResponse

IdLike = UUID | str


class LabelsMixin:
    """Label endpoints."""

    async def list_labels(self, project_id: IdLike) -> LabelsResponse:
        """Lists a project's labels.

        ``GET /projects/{project_id}/labels``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelsResponse,
            "GET",
            f"projects/{project_id}/labels",
            rate_class=RateClass.TIER2,
            route="GET /projects/{project_id}/labels",
            concurrency=Concurrency.NONE,
        )

    async def create_label(self, project_id: IdLike, name: str, color: str | None = None) -> Label:
        """Creates a label. A project may have at most 10,000 labels.

        ``POST /projects/{project_id}/labels``
        """
        body: dict[str, object] = {"name": name}
        if color is not None:
            body["color"] = color
        return await self._send_json(  # type: ignore[attr-defined]
            Label,
            "POST",
            f"projects/{project_id}/labels",
            rate_class=RateClass.WRITES,
            route="POST /projects/{project_id}/labels",
            concurrency=Concurrency.NONE,
            json_body=body,
        )

    async def update_label(
        self,
        label_id: IdLike,
        name: str | None = None,
        color: str | None = None,
    ) -> Label:
        """Updates a label's name and/or color.

        ``PATCH /labels/{label_id}``
        """
        body: dict[str, object] = {}
        if name is not None:
            body["name"] = name
        if color is not None:
            body["color"] = color
        return await self._send_json(  # type: ignore[attr-defined]
            Label,
            "PATCH",
            f"labels/{label_id}",
            rate_class=RateClass.WRITES,
            route="PATCH /labels/{label_id}",
            concurrency=Concurrency.NONE,
            json_body=body,
        )

    async def delete_label(self, label_id: IdLike) -> OkResponse:
        """Deletes a label.

        ``DELETE /labels/{label_id}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"labels/{label_id}",
            rate_class=RateClass.WRITES,
            route="DELETE /labels/{label_id}",
            concurrency=Concurrency.NONE,
        )

    async def label_items(self, label_id: IdLike) -> LabelItems:
        """Lists the sprites, sounds and saved animations tagged with a label.

        ``GET /labels/{label_id}/items``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelItems,
            "GET",
            f"labels/{label_id}/items",
            rate_class=RateClass.TIER2,
            route="GET /labels/{label_id}/items",
            concurrency=Concurrency.NONE,
        )

    async def set_label_thumbnail(self, label_id: IdLike, asset_id: IdLike | None = None) -> Label:
        """Sets or clears a label's cover thumbnail.

        ``POST /labels/{label_id}/thumbnail``
        """
        body = {"asset_id": str(asset_id) if asset_id is not None else None}
        return await self._send_json(  # type: ignore[attr-defined]
            Label,
            "POST",
            f"labels/{label_id}/thumbnail",
            rate_class=RateClass.WRITES,
            route="POST /labels/{label_id}/thumbnail",
            concurrency=Concurrency.NONE,
            json_body=body,
        )

    async def associate_asset_label(self, asset_id: IdLike, name: str) -> LabelAssociation:
        """Adds a label to a sprite asset.

        ``POST /assets/{asset_id}/labels``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "POST",
            f"assets/{asset_id}/labels",
            rate_class=RateClass.WRITES,
            route="POST /assets/{asset_id}/labels",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def remove_asset_label(self, asset_id: IdLike, name: str) -> LabelAssociation:
        """Removes a label from a sprite asset.

        ``DELETE /assets/{asset_id}/labels?name={name}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "DELETE",
            f"assets/{asset_id}/labels",
            rate_class=RateClass.WRITES,
            route="DELETE /assets/{asset_id}/labels",
            concurrency=Concurrency.NONE,
            params=[("name", name)],
        )

    async def dismiss_asset_label_suggestion(self, asset_id: IdLike, name: str) -> OkResponse:
        """Dismisses a suggested label for a sprite asset.

        ``DELETE /assets/{asset_id}/label-suggestions?name={name}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"assets/{asset_id}/label-suggestions",
            rate_class=RateClass.WRITES,
            route="DELETE /assets/{asset_id}/label-suggestions",
            concurrency=Concurrency.NONE,
            params=[("name", name)],
        )

    async def associate_sound_label(self, asset_id: IdLike, name: str) -> LabelAssociation:
        """Adds a label to a sound asset.

        ``POST /sound-assets/{asset_id}/labels``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "POST",
            f"sound-assets/{asset_id}/labels",
            rate_class=RateClass.WRITES,
            route="POST /sound-assets/{asset_id}/labels",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def remove_sound_label(self, asset_id: IdLike, name: str) -> LabelAssociation:
        """Removes a label from a sound asset.

        ``DELETE /sound-assets/{asset_id}/labels?name={name}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "DELETE",
            f"sound-assets/{asset_id}/labels",
            rate_class=RateClass.WRITES,
            route="DELETE /sound-assets/{asset_id}/labels",
            concurrency=Concurrency.NONE,
            params=[("name", name)],
        )

    async def dismiss_sound_label_suggestion(self, asset_id: IdLike, name: str) -> OkResponse:
        """Dismisses a suggested label for a sound asset.

        ``DELETE /sound-assets/{asset_id}/label-suggestions?name={name}``
        """
        return await self._send_ack(  # type: ignore[attr-defined]
            "DELETE",
            f"sound-assets/{asset_id}/label-suggestions",
            rate_class=RateClass.WRITES,
            route="DELETE /sound-assets/{asset_id}/label-suggestions",
            concurrency=Concurrency.NONE,
            params=[("name", name)],
        )

    async def associate_saved_animation_label(
        self, saved_id: IdLike, name: str
    ) -> LabelAssociation:
        """Adds a label to a saved animation.

        ``POST /saved-animations/{id}/labels``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "POST",
            f"saved-animations/{saved_id}/labels",
            rate_class=RateClass.WRITES,
            route="POST /saved-animations/{id}/labels",
            concurrency=Concurrency.NONE,
            json_body={"name": name},
        )

    async def remove_saved_animation_label(self, saved_id: IdLike, name: str) -> LabelAssociation:
        """Removes a label from a saved animation.

        ``DELETE /saved-animations/{id}/labels?name={name}``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            LabelAssociation,
            "DELETE",
            f"saved-animations/{saved_id}/labels",
            rate_class=RateClass.WRITES,
            route="DELETE /saved-animations/{id}/labels",
            concurrency=Concurrency.NONE,
            params=[("name", name)],
        )


__all__ = ["LabelsMixin"]
