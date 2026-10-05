# GameTorch Python SDK

The official Python SDK for the [GameTorch](https://gametorch.app) API.
GameTorch generates game-ready **sprites**, **sound effects** and **animations**
from text prompts and organizes them into projects.

- [API reference](https://gametorch.app/api/docs)
- [Agent / LLM guide](https://gametorch.app/llms.txt)
- [Privacy policy](https://gametorch.app/privacy)
- [Terms and conditions](https://gametorch.app/terms)

## Features

- Full coverage of the public GameTorch API, with strongly typed request and
  response models built on [pydantic](https://docs.pydantic.dev).
- Both an async client (`AsyncClient`, built on
  [httpx](https://www.python-httpx.org)) and a matching synchronous `Client`.
- Polite by default: client-side rate limiting that mirrors GameTorch's
  published limits, concurrency caps, and automatic retries with exponential
  backoff that honors `Retry-After`.
- Cursor pagination with `Paginator` helpers supporting both `async for` and
  `for`.
- Accurate money handling with `decimal.Decimal` (100 credits = $1).
- Sensible errors with status-code helpers.
- MIT licensed.

## Installation

```sh
pip install gametorch
# or
uv add gametorch
```

Python 3.11+ is required.

## Quickstart

```python
import asyncio
from gametorch import AsyncClient, SpriteMode


async def main() -> None:
    # Reads GAMETORCH_API_KEY; or pass api_key="gt2_..." explicitly.
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
        print(f"generation {job.id} is {job.status}")


asyncio.run(main())
```

The synchronous client has the same surface:

```python
from gametorch import Client, SpriteMode

with Client.from_env() as client:
    models = client.sprite_models()
    project = client.create_project("My Game")
    job = (
        client.generate_sprite(project.id)
        .prompt("a red fox, side view")
        .mode(SpriteMode.SINGLE)
        .image_model(models.image_models[0].id)
        .send()
    )
    print(f"generation {job.id} is {job.status}")
```

## Authentication

Every request uses `Authorization: Bearer <token>`, where the token is either a
server-to-server API key (`gt2_...`) or a Clerk session token:

```python
from gametorch import AsyncClient

# API key (server-to-server)
client = AsyncClient(api_key="gt2_...")

# Clerk session token (browser / trusted backend)
client = AsyncClient(bearer_token="eyJ...")
```

Create an API key from the GameTorch dashboard or with `create_key`. Keys are
shown only once and can carry a spend limit.

### Key scopes

Every API key has a `key_scope` fixed at creation:

- `admin` — full access to the owning account/organization.
- `project_write` — bound to one project: read and write its content.
- `project_read` — bound to one project: read-only.

```python
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from gametorch import ApiKeyScope, CreateApiKeyRequest, SpendResetCadence

expires_at = datetime.now(timezone.utc) + timedelta(days=30)
read = await client.create_key(
    CreateApiKeyRequest.project_read(project.id)
    .name("CI read key")
    .max_spend_limit(Decimal(0))
    .spend_reset_cadence(SpendResetCadence.MONTHLY)
    .expires_at(expires_at)
)
print(read.key.key_scope, read.key.project_id)
```

## Base URL

The SDK defaults to `https://gametorch.app/api`. For local development, point it
at your local deployment:

```python
client = AsyncClient(api_key="gt2_local_dev_key", base_url="http://localhost:8300/api")
```

You can also set `GAMETORCH_BASE_URL`.

## Rate limits

GameTorch rate limits every account per route and returns `429` when a limit is
exceeded. The SDK is respectful by default:

- Throttles **Tier 1** routes (generation creates, frame generation, animation
  exports) to 1 request/second per route.
- Throttles **Tier 2** routes (content, usage, search, single-item reads) to
  2 requests/second per route.
- Shares a **token bucket** (100-request burst, 5 requests/second refill) across
  unbounded writes.
- Caps in-flight hold-creating requests at 25 and concurrent frame generations
  at 5.
- Retries `429`, `408` and `5xx` responses with exponential backoff and jitter,
  honoring `Retry-After`.

Tune or disable this behavior:

```python
client = AsyncClient(
    api_key="gt2_...",
    max_retries=5,
    retry_base_delay=0.25,
    rate_limit=False,  # only if you manage limits yourself
)
```

## Pagination

List endpoints accept `ListParams` and return a page with a `next_cursor`. The
`stream_*` helpers fetch pages on demand:

```python
stream = client.stream_generations(project.id, include_archived=False)
async for generation in stream:
    print(generation.id)
```

## Filtering animations by base image

Animation runs link back to the sprite asset they were generated from via
`base_asset_id` (``None`` when generated from scratch). You can filter animation
queries by it:

```python
from gametorch import ListParams

runs = await client.list_animation_runs(project.id, ListParams(base_asset_id=sprite.id))
for run in runs.animations:
    print(run.id, run.base_asset_id)
```

## Provenance

Generation and asset responses expose who or what created them. The fields are
flattened onto the resource as `provenance` (`user_id`, `source`, `api_key_id`,
`key_name`):

```python
generation = await client.get_generation(generation_id)
print(generation.provenance.user_id, generation.provenance.source)
```

## Error handling

Every fallible operation raises a subclass of `GametorchError`. `ApiError`
exposes the HTTP status, the API's `error` message and convenience predicates:

```python
from gametorch import ApiError, GametorchError

try:
    asset = await client.get_asset(asset_id)
except ApiError as err:
    if err.is_not_found():
        print("no such asset")
    elif err.is_rate_limited():
        print("slow down")
    else:
        raise
```

## API coverage

| Area | Methods |
| --- | --- |
| Catalog | `sprite_models`, `sound_models`, `animation_models` |
| Projects | `list_projects`, `create_project`, `rename_project`, `delete_project` |
| Sprites | `generate_sprite`, `list_generations`, `get_generation`, `list_sprite_assets`, `get_asset`, `asset_content`, `asset_original`, `rename_asset`, `put_asset_metadata`, `archive_asset`, `unarchive_asset`, `delete_asset`, `archive_generation`, `unarchive_generation`, `delete_generation` |
| Sounds | `generate_sound`, `list_sound_generations`, `get_sound_generation`, `sound_asset_content`, `rename_sound_asset`, `put_sound_asset_metadata`, `archive_sound_asset`, `unarchive_sound_asset`, `delete_sound_asset`, `archive_sound_generation`, `unarchive_sound_generation` |
| Animations | `estimate_animation`, `generate_animation`, `list_animation_runs`, `get_animation_run`, `animation_content`, `archive_animation_run`, `unarchive_animation_run`, `delete_animation_run`, `generate_frames`, `frame_content`, `frame_content_by_number` |
| Exports | `export_plan`, `export`, `export_texturepacker`, `export_texturepacker_zip`, `export_aseprite`, `export_godot`, `export_godot_zip`, `export_grid`, `export_gamemaker`, `export_sequence_zip` |
| Saved animations | `list_saved_animations`, `save_animation`, `get_saved_animation`, `rename_saved_animation`, `put_saved_animation_metadata`, `archive_saved_animation`, `unarchive_saved_animation`, `delete_saved_animation` |
| Labels | `list_labels`, `create_label`, `update_label`, `delete_label`, `label_items`, `set_label_thumbnail`, `associate_asset_label`, `remove_asset_label`, `dismiss_asset_label_suggestion`, `associate_sound_label`, `remove_sound_label`, `dismiss_sound_label_suggestion`, `associate_saved_animation_label`, `remove_saved_animation_label` |
| Art styles | `list_art_styles`, `create_art_style`, `generate_art_style`, `delete_art_style` |
| Usage | `usage`, `usage_histogram` |
| API keys | `list_keys`, `create_key`, `update_key`, `delete_key` |
| Account | `ensure_user`, `health` |

## Examples

Runnable examples live in [`examples/`](examples):

```sh
export GAMETORCH_API_KEY=gt2_...
python examples/list_projects.py
python examples/generate_sprite.py       # spends credits
python examples/generate_sound.py        # spends credits
python examples/generate_animation.py    # spends credits
python examples/export_animation.py      # read-only; exports every format
python examples/create_admin_key.py      # needs an admin key
python examples/create_project_keys.py   # needs an admin key
GAMETORCH_PROJECT=<project-uuid> python examples/stream_generations.py
```

## Testing

`pytest` runs the offline unit and fixture tests by default. The live suites are
opt-in so they never hit the network or spend credits unless you ask:

| Suite | Env vars | Spends credits |
| --- | --- | --- |
| `tests/live` | `GAMETORCH_API_KEY` | No (read-only + free estimate) |
| `tests/live_writes` | `GAMETORCH_API_KEY`, `GAMETORCH_LIVE_WRITES=1` | No (creates and cleans up its own data) |
| `tests/live_spend` | `GAMETORCH_API_KEY`, `GAMETORCH_LIVE_SPEND=1` | **Yes** |

```sh
GAMETORCH_API_KEY=gt2_... GAMETORCH_BASE_URL=http://localhost:8300/api \
  pytest -m live -s

GAMETORCH_API_KEY=gt2_... GAMETORCH_LIVE_WRITES=1 \
  pytest -m live_writes -s

# Costs money: generates a sprite, a sound and a 4s animation plus exports.
GAMETORCH_API_KEY=gt2_... GAMETORCH_LIVE_SPEND=1 \
  pytest -m live_spend -s
```

The live tests and the generation examples each create their own project. By
default they delete it again at the end; set `GAMETORCH_KEEP_PROJECT=1` to keep
the project so you can inspect it in the GameTorch UI.

## License

MIT. See [LICENSE](LICENSE).
