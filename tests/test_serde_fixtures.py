"""Deserialization tests against representative API payloads.

These fixtures mirror the wire format (including fields where the running
service differs from the OpenAPI schema, such as ``assets_delivered`` being an
integer and ``dismissed_suggestions`` being an array).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from gametorch import (
    ApiKey,
    ApiKeyScope,
    ArchiveResponse,
    ExportPlan,
    Generation,
    JobCreated,
    LabelAssociation,
    LabelItems,
    SpriteModels,
    UsageHistogram,
)
from gametorch.models import AnimationRun


def test_reservation_uses_boolean_created() -> None:
    json = """
    {
        "id": "b58cc74c-ea81-4a9b-b418-d785192011a4",
        "status": "queued",
        "created": true,
        "reserved_credits": "300.000000000000"
    }
    """
    reservation = JobCreated.model_validate_json(json)
    assert reservation.created is True
    assert str(reservation.reserved_credits) == "300.000000000000"


def test_sprite_generation_tolerates_int_assets_and_array_suggestions() -> None:
    json = """
    {
        "id": "b58cc74c-ea81-4a9b-b418-d785192011a4",
        "project_id": "afb90af1-80a4-4c75-9328-2de4edde4b16",
        "prompt": "fauna you'd find in a Western video game",
        "mode": "multiple",
        "image_model": "black-forest-labs/flux-3-image",
        "text_model": "openai/gpt-6-luna",
        "quality": null,
        "resolution": "1K",
        "base_asset_id": null,
        "status": "succeeded",
        "credits_consumed": "5.003952358800",
        "reserved_credits": "0.000000000000",
        "assets_delivered": 4,
        "archived_assets": 0,
        "error": null,
        "label_suggestions": ["enemy", "fauna"],
        "art_style_suggestion": null,
        "created_at": "2026-10-01T21:10:48.237007+00:00",
        "completed_at": "2026-10-01T21:11:22.052778+00:00",
        "archived_at": null,
        "user_id": "user_3JvOvirRbpZA5wZsIh3wgoRqYCQ",
        "source": "API key",
        "api_key_id": "93d6fe0b-b513-45cc-940c-2e8dc168f130",
        "key_name": "ci",
        "assets": [
            {
                "id": "857f82f2-f5a7-445f-a97d-a30097434324",
                "name": null,
                "width": 473,
                "height": 342,
                "archived_at": null,
                "has_original": true,
                "metadata": {},
                "labels": ["fauna"],
                "dismissed_suggestions": [],
                "generation_id": null,
                "project_id": null,
                "created_at": null,
                "prompt": null,
                "user_id": "user_abc",
                "source": "API key",
                "api_key_id": "93d6fe0b-b513-45cc-940c-2e8dc168f130",
                "key_name": null
            }
        ]
    }
    """
    generation = Generation.model_validate_json(json)
    assert generation.assets_delivered == 4
    assert len(generation.label_suggestions) == 2
    assert len(generation.assets) == 1
    assert generation.assets[0].width == 473
    assert generation.assets[0].has_original is True

    assert generation.provenance.source == "API key"
    assert generation.provenance.user_id == "user_3JvOvirRbpZA5wZsIh3wgoRqYCQ"
    assert generation.provenance.api_key_id is not None
    assert generation.assets[0].provenance.user_id == "user_abc"


def test_sprite_catalog_decodes() -> None:
    json = """
    {
        "default_text_model": "openai/gpt-6-luna",
        "empirical_evidence": "v2/notes/sprite-provider-costs.md",
        "image_models": [
            {
                "id": "openai/gpt-image-2.5-flare",
                "name": "GPT Image 2.5 Flare",
                "blurb": "Best suited for base generation.",
                "available": true,
                "unavailable_reason": null,
                "qualities": ["auto", "low", "medium", "high"],
                "resolutions": [],
                "native_transparency": true,
                "editing": false,
                "transparency_status": "empirically_verified",
                "default_quality": "medium",
                "default_resolution": null,
                "default_canvas_size": "1024x1024",
                "capabilities_url": "https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.5-flare/endpoints",
                "reservation_credits": "5.000000000000"
            }
        ],
        "modes": ["single", "multiple"],
        "multiple_layout": {"rows": 2, "columns": 2, "images_per_request": 1},
        "reservation_credits": 300,
        "resolution_note": "Resolution describes the entire canvas.",
        "resolution_scope": "whole_canvas",
        "text_models": [{"id": "none", "name": "No prompt enhancement"}],
        "verified_at": "2026-09-27"
    }
    """
    catalog = SpriteModels.model_validate_json(json)
    assert len(catalog.image_models) == 1
    assert catalog.reservation_credits == Decimal(300)
    assert catalog.multiple_layout.columns == 2
    assert catalog.image_models[0].reservation_credits == Decimal("5.000000000000")


def test_animation_run_decodes() -> None:
    json = """
    {
        "id": "29dc50d6-f8da-44c7-afa2-c2f5dcbd3cbb",
        "project_id": "afb90af1-80a4-4c75-9328-2de4edde4b16",
        "prompt": "show him draw his pistol and aim to the right",
        "animation_model": "ash",
        "duration": 4,
        "animation": {
            "id": "23d05f16-46f0-4672-8562-a9b90a9a46fb",
            "duration_seconds": 4,
            "resolution": "720p",
            "created_at": "2026-10-01T02:06:52.153372+00:00"
        },
        "status": "succeeded",
        "credits_consumed": "73.347960000000",
        "reserved_credits": "0.000000000000",
        "assets_delivered": 1,
        "base_asset_id": "6021352a-ab35-4a17-960b-71d30adf53a0",
        "error": null,
        "created_at": "2026-10-01T02:04:15.744412+00:00",
        "completed_at": "2026-10-01T02:06:52.157269+00:00",
        "archived_at": null,
        "frame_runs": [
            {
                "id": "3241879e-833f-4dee-b6a6-a19661102893",
                "status": "succeeded",
                "fps": 12,
                "frame_count": 49,
                "credits_consumed": "3.282263405160",
                "reserved_credits": "0.000000000000",
                "error": null,
                "created_at": "2026-10-01T02:06:52.155037+00:00"
            }
        ],
        "frames": [
            {
                "id": "a2efe498-fa0b-4a65-a2a1-d24edd554954",
                "frame_number": 1,
                "generation_id": "3241879e-833f-4dee-b6a6-a19661102893",
                "created_at": "2026-10-01T02:06:55.498587+00:00"
            }
        ]
    }
    """
    run = AnimationRun.model_validate_json(json)
    assert run.animation_model == "ash"
    assert run.animation is not None
    assert run.animation.resolution == "720p"
    assert run.frame_runs[0].fps == 12
    assert run.frames[0].frame_number == 1


def test_usage_histogram_decodes_sources() -> None:
    json = """
    {
        "range": "24h",
        "width_seconds": 3600,
        "sources": [{"id": "api_key:abc", "label": "My Key", "kind": "api_key"}],
        "buckets": [
            {
                "start": "2026-10-04T01:00:00Z",
                "end": "2026-10-04T02:00:00Z",
                "total": "0",
                "values": {"api_key:abc": "0"}
            }
        ]
    }
    """
    histogram = UsageHistogram.model_validate_json(json)
    assert histogram.sources[0].id == "api_key:abc"
    assert str(histogram.buckets[0].total) == "0"
    assert str(histogram.buckets[0].values["api_key:abc"]) == "0"


def test_export_plan_decodes() -> None:
    json = """
    {
        "start_frame": 1,
        "end_frame": 4,
        "reference": {"bounds": [2, 2, 433, 974], "image_width": 437, "image_height": 978},
        "first_frame": {"frame_number": 1, "image_width": 720, "image_height": 1280, "bounds": [115, 89, 490, 1102]},
        "frames": [
            {
                "frame_number": 1,
                "image_width": 720,
                "image_height": 1280,
                "bounds": [115, 89, 490, 1102],
                "offset_x": 0,
                "offset_y": 1,
                "scaled_width": 433,
                "scaled_height": 974
            }
        ],
        "max_width": 490,
        "max_height": 1104,
        "scale": 0.8838475499092558,
        "scale_width": 0.8836734693877552,
        "scale_height": 0.8838475499092558,
        "canvas_width": 433,
        "canvas_height": 976,
        "frame_count": 4
    }
    """
    plan = ExportPlan.model_validate_json(json)
    assert plan.frame_count == 4
    assert plan.first_frame is not None
    assert plan.first_frame.frame_number == 1
    assert plan.frames[0].scaled_width == 433


def test_label_items_decodes() -> None:
    json = """
    {
        "label": {
            "id": "7fb262e8-6697-4d3f-b055-073874ce786e",
            "name": "enemy",
            "color": "#e57b7b",
            "thumbnail_asset_id": "ebe4fcb6-abaf-4a9e-84d6-b460d87e10a6",
            "created_at": "2026-09-28T21:07:15.245443Z"
        },
        "assets": [
            {
                "id": "7cf2e92f-5fe8-420e-8684-75017f01f766",
                "width": 955,
                "height": 1001,
                "archived_at": null,
                "name": null,
                "has_original": true,
                "metadata": {},
                "generation_id": "c4edd487-1b17-4d9a-b9cd-c6cfed1cfe9d",
                "prompt": "make its eyes solid black",
                "created_at": "2026-10-01T18:11:15.153977+00:00",
                "labels": ["enemy", "fauna"]
            }
        ],
        "sounds": [],
        "saved_animations": []
    }
    """
    items = LabelItems.model_validate_json(json)
    assert items.label.name == "enemy"
    assert items.assets[0].width == 955


def test_archive_response_decodes() -> None:
    json = '{"ok": true, "archived_at": "2026-09-29T19:49:33.368293+00:00"}'
    response = ArchiveResponse.model_validate_json(json)
    assert response.ok is True
    assert response.archived_at is not None


def test_label_association_decodes() -> None:
    json = '{"ok": true, "labels": ["character", "cowboy"]}'
    association = LabelAssociation.model_validate_json(json)
    assert association.labels == ["character", "cowboy"]


def test_api_key_scopes_decode() -> None:
    read = """
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Read-only CI key",
        "key_prefix": "gt2_abc",
        "expires_at": null,
        "max_spend_limit": "0",
        "spend_reset_cadence": "monthly",
        "key_scope": "project_read",
        "project_id": "22222222-2222-2222-2222-222222222222",
        "spend": "0.000000000000",
        "lifetime_spend": "0.000000000000",
        "spend_reset_at": null,
        "created_at": "2026-10-05T00:00:00Z"
    }
    """
    key = ApiKey.model_validate_json(read)
    assert key.key_scope is ApiKeyScope.PROJECT_READ
    assert key.project_id == UUID("22222222-2222-2222-2222-222222222222")

    write = """
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "Write CI key",
        "key_prefix": "gt2_def",
        "expires_at": null,
        "max_spend_limit": "500",
        "spend_reset_cadence": "weekly",
        "key_scope": "project_write",
        "project_id": "22222222-2222-2222-2222-222222222222",
        "spend": "0.000000000000",
        "lifetime_spend": "0.000000000000",
        "spend_reset_at": null,
        "created_at": "2026-10-05T00:00:00Z"
    }
    """
    key = ApiKey.model_validate_json(write)
    assert key.key_scope is ApiKeyScope.PROJECT_WRITE

    admin = """
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "key_prefix": "gt2_ghi",
        "spend_reset_cadence": "never",
        "key_scope": "admin",
        "project_id": null,
        "spend": "0",
        "lifetime_spend": "0",
        "created_at": "2026-10-05T00:00:00Z"
    }
    """
    key = ApiKey.model_validate_json(admin)
    assert key.key_scope is ApiKeyScope.ADMIN
    assert key.project_id is None


def test_lenient_helpers_accept_odd_shapes() -> None:
    from gametorch.models import Asset

    asset = Asset.model_validate(
        {
            "id": "857f82f2-f5a7-445f-a97d-a30097434324",
            "assets_delivered": True,
            "dismissed_suggestions": None,
        }
    )
    assert asset.dismissed_suggestions == []

    asset = Asset.model_validate(
        {
            "id": "857f82f2-f5a7-445f-a97d-a30097434324",
            "dismissed_suggestions": 3,
        }
    )
    assert asset.dismissed_suggestions == []


def test_api_key_with_secret_exposes_key_view() -> None:
    from gametorch import ApiKeyWithSecret

    created = ApiKeyWithSecret.model_validate(
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "key_prefix": "gt2_ghi",
            "spend_reset_cadence": "never",
            "key_scope": "admin",
            "project_id": None,
            "spend": "0",
            "lifetime_spend": "0",
            "created_at": "2026-10-05T00:00:00Z",
            "key_full": "gt2_secret",
        }
    )
    assert created.key_full == "gt2_secret"
    assert created.key.id == UUID("44444444-4444-4444-4444-444444444444")
