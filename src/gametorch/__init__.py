"""Official Python SDK for the `GameTorch <https://gametorch.app>`_ API.

GameTorch generates game-ready **sprites**, **sound effects** and
**animations** from text prompts and organizes them into projects.

- API reference: https://gametorch.app/api/docs
- Agent / LLM guide: https://gametorch.app/llms.txt
- Privacy policy: https://gametorch.app/privacy
- Terms and conditions: https://gametorch.app/terms

Quickstart::

    import asyncio
    from gametorch import AsyncClient, SpriteMode

    async def main() -> None:
        async with AsyncClient.from_env() as client:
            models = await client.sprite_models()
            project = await client.create_project("My Game")
            job = await (
                client.generate_sprite(project.id)
                .prompt("a red fox, side view")
                .mode(SpriteMode.SINGLE)
                .image_model(models.image_models[0].id)
                .send()
            )
            print(job.id, job.status)

    asyncio.run(main())

A synchronous :class:`Client` with the same API is also available.
"""

from __future__ import annotations

from ._api.animations import (
    AnimationEstimateBuilder,
    AnimationRunBuilder,
    FrameGenerationBuilder,
)
from ._api.saved_animations import SaveAnimationBuilder
from ._api.sounds import SoundGenerationBuilder
from ._api.sprites import SpriteGenerationBuilder
from ._client import (
    DEFAULT_BASE_URL,
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_BEARER_TOKEN,
    AsyncClient,
)
from ._errors import (
    ApiError,
    ConfigError,
    DecodeError,
    GametorchError,
    HttpError,
    InvalidBaseUrlError,
    RateLimitedError,
)
from ._sync import Client
from ._types import (
    ApiKeyScope,
    ArchiveResponse,
    AssetMetadataResponse,
    AssetNameResponse,
    Download,
    ExportFormat,
    JobCreated,
    ListParams,
    OkResponse,
    Page,
    Paginator,
    SpendResetCadence,
    SpriteMode,
    credits_to_usd,
)
from ._version import __version__
from .models import (
    AnimationAsset,
    AnimationEstimate,
    AnimationFrame,
    AnimationModelInfo,
    AnimationModels,
    AnimationRun,
    AnimationsResponse,
    ApiKey,
    ApiKeyWithSecret,
    ArtStyle,
    ArtStylesResponse,
    ArtStyleSuggestion,
    Asset,
    CreateApiKeyRequest,
    Export,
    ExportFrame,
    ExportPlan,
    ExportReference,
    FrameRun,
    Generation,
    GenerationsResponse,
    GodotExport,
    HistogramBucket,
    ImageModel,
    KeysResponse,
    Label,
    LabelAsset,
    LabelAssociation,
    LabelItems,
    LabelSavedAnimation,
    LabelSound,
    LabelsResponse,
    MultipleLayout,
    Project,
    ProjectsResponse,
    Provenance,
    SavedAnimation,
    SavedAnimationsResponse,
    SoundAsset,
    SoundGeneration,
    SoundGenerationsResponse,
    SoundModelInfo,
    SoundModels,
    SpriteAssetsResponse,
    SpriteModels,
    TextModel,
    TexturePackerExport,
    UpdateApiKeyRequest,
    Usage,
    UsageHistogram,
    UsageHistogramSource,
    UsageRecord,
    UsageSummary,
)

__all__ = [  # noqa: RUF022 - grouped for readability
    # Clients
    "AsyncClient",
    "Client",
    # Constants
    "DEFAULT_BASE_URL",
    "ENV_API_KEY",
    "ENV_BASE_URL",
    "ENV_BEARER_TOKEN",
    "__version__",
    # Errors
    "ApiError",
    "ConfigError",
    "DecodeError",
    "GametorchError",
    "HttpError",
    "InvalidBaseUrlError",
    "RateLimitedError",
    # Types / enums
    "ApiKeyScope",
    "ArchiveResponse",
    "AssetMetadataResponse",
    "AssetNameResponse",
    "Download",
    "ExportFormat",
    "JobCreated",
    "ListParams",
    "OkResponse",
    "Page",
    "Paginator",
    "SpendResetCadence",
    "SpriteMode",
    "credits_to_usd",
    # Builders
    "AnimationEstimateBuilder",
    "AnimationRunBuilder",
    "FrameGenerationBuilder",
    "SaveAnimationBuilder",
    "SoundGenerationBuilder",
    "SpriteGenerationBuilder",
    # Models
    "AnimationAsset",
    "AnimationEstimate",
    "AnimationFrame",
    "AnimationModelInfo",
    "AnimationModels",
    "AnimationRun",
    "AnimationsResponse",
    "ApiKey",
    "ApiKeyWithSecret",
    "ArtStyle",
    "ArtStyleSuggestion",
    "ArtStylesResponse",
    "Asset",
    "CreateApiKeyRequest",
    "Export",
    "ExportFrame",
    "ExportPlan",
    "ExportReference",
    "FrameRun",
    "Generation",
    "GenerationsResponse",
    "GodotExport",
    "HistogramBucket",
    "ImageModel",
    "KeysResponse",
    "Label",
    "LabelAsset",
    "LabelAssociation",
    "LabelItems",
    "LabelSavedAnimation",
    "LabelSound",
    "LabelsResponse",
    "MultipleLayout",
    "Project",
    "ProjectsResponse",
    "Provenance",
    "SavedAnimation",
    "SavedAnimationsResponse",
    "SoundAsset",
    "SoundGeneration",
    "SoundGenerationsResponse",
    "SoundModelInfo",
    "SoundModels",
    "SpriteAssetsResponse",
    "SpriteModels",
    "TextModel",
    "TexturePackerExport",
    "UpdateApiKeyRequest",
    "Usage",
    "UsageHistogram",
    "UsageHistogramSource",
    "UsageRecord",
    "UsageSummary",
]
