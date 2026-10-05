"""A synchronous facade over :class:`~gametorch.AsyncClient`.

The sync client owns a background event loop thread and forwards every public
operation to an internal :class:`AsyncClient`. Builders and paginators returned
by the sync client are wired to run synchronously, so the same fluent code works
in both worlds.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
from typing import Any

from ._client import AsyncClient

__all__ = ["Client"]

_FACTORY_METHODS = frozenset(
    {
        "generate_sprite",
        "generate_sound",
        "generate_animation",
        "estimate_animation",
        "generate_frames",
        "save_animation",
        "stream_generations",
        "stream_sound_generations",
        "stream_animation_runs",
        "stream_saved_animations",
        "stream_usage",
    }
)


def _operation_names() -> list[str]:
    names: list[str] = []
    for name in dir(AsyncClient):
        if name.startswith("_"):
            continue
        if name in _FACTORY_METHODS:
            names.append(name)
            continue
        attr = getattr(AsyncClient, name, None)
        if inspect.iscoroutinefunction(attr):
            names.append(name)
    return names


def _make_proxy(name: str):
    def method(self: Client, *args: Any, **kwargs: Any) -> Any:
        result = getattr(self._async, name)(*args, **kwargs)
        if inspect.iscoroutine(result):
            return self._run(result)
        if hasattr(result, "_dispatch"):
            result._dispatch = self._dispatch
        return result

    method.__name__ = name
    method.__qualname__ = f"Client.{name}"
    method.__doc__ = getattr(AsyncClient, name).__doc__
    return method


class Client:
    """A synchronous client for the GameTorch API.

    Example::

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
            print(job.id, job.status)
    """

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = dict(kwargs)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="gametorch-sync", daemon=True
        )
        self._thread.start()
        self._closed = False
        self._async = self._run(_create_async_client(kwargs))

    # -- Construction helpers -------------------------------------------------

    @classmethod
    def from_env(cls, **overrides: Any) -> Client:
        """Builds a client from ``GAMETORCH_API_KEY`` / ``GAMETORCH_BASE_URL``."""
        import os

        from ._client import ENV_API_KEY, ENV_BASE_URL, ENV_BEARER_TOKEN

        params: dict[str, Any] = {}
        api_key = os.environ.get(ENV_API_KEY)
        if api_key:
            params["api_key"] = api_key
        elif os.environ.get(ENV_BEARER_TOKEN):
            params["bearer_token"] = os.environ[ENV_BEARER_TOKEN]
        if os.environ.get(ENV_BASE_URL):
            params["base_url"] = os.environ[ENV_BASE_URL]
        params.update(overrides)
        return cls(**params)

    def clone(self) -> Client:
        """Returns an independent sync client with the same configuration."""
        return Client(**self._kwargs)

    # -- Introspection --------------------------------------------------------

    @property
    def base_url(self) -> str:
        """The base URL this client talks to, including the ``/api`` suffix."""
        return self._async.base_url

    @property
    def is_authenticated(self) -> bool:
        """Whether the client is authenticated."""
        return self._async.is_authenticated

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(base_url={self.base_url!r}, "
            f"authenticated={self.is_authenticated!r})"
        )

    # -- Bridging -------------------------------------------------------------

    def _run(self, awaitable: Any) -> Any:
        future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
        return future.result()

    def _dispatch(self, awaitable: Any) -> Any:
        return self._run(awaitable)

    # -- Lifecycle ------------------------------------------------------------

    def close(self) -> None:
        """Closes the HTTP connection pool and stops the background loop."""
        if self._closed:
            return
        self._closed = True
        try:
            self._run(self._async.aclose())
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
            self._loop.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


async def _create_async_client(kwargs: dict[str, Any]) -> AsyncClient:
    return AsyncClient(**kwargs)


for _name in _operation_names():
    setattr(Client, _name, _make_proxy(_name))
