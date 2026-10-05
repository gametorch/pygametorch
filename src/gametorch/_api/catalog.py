"""Catalog endpoints."""

from __future__ import annotations

from .._rate_limit import Concurrency, RateClass
from ..models import AnimationModels, SoundModels, SpriteModels


class CatalogMixin:
    """Sprite, sound and animation model catalogs."""

    async def sprite_models(self) -> SpriteModels:
        """Returns the image-model catalog, text models, modes and reservations.

        ``GET /sprite-models``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            SpriteModels,
            "GET",
            "sprite-models",
            rate_class=RateClass.TIER2,
            route="GET /sprite-models",
            concurrency=Concurrency.NONE,
        )

    async def sound_models(self) -> SoundModels:
        """Returns the sound-model catalog and supported output formats.

        ``GET /sound-models``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            SoundModels,
            "GET",
            "sound-models",
            rate_class=RateClass.TIER2,
            route="GET /sound-models",
            concurrency=Concurrency.NONE,
        )

    async def animation_models(self) -> AnimationModels:
        """Returns the animation models by their public names.

        ``GET /animation-models``
        """
        return await self._send_json(  # type: ignore[attr-defined]
            AnimationModels,
            "GET",
            "animation-models",
            rate_class=RateClass.TIER2,
            route="GET /animation-models",
            concurrency=Concurrency.NONE,
        )
