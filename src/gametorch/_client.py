"""The GameTorch :class:`AsyncClient` and shared request machinery."""

from __future__ import annotations

import asyncio
import json
import os
import random
from collections.abc import Awaitable
from typing import Any, TypeVar
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, ValidationError

from ._api.account import AccountMixin
from ._api.animations import AnimationsMixin
from ._api.art_styles import ArtStylesMixin
from ._api.catalog import CatalogMixin
from ._api.exports import ExportsMixin
from ._api.keys import KeysMixin
from ._api.labels import LabelsMixin
from ._api.projects import ProjectsMixin
from ._api.saved_animations import SavedAnimationsMixin
from ._api.sounds import SoundsMixin
from ._api.sprites import SpritesMixin
from ._api.usage import UsageMixin
from ._errors import (
    ApiError,
    ConfigError,
    DecodeError,
    HttpError,
    InvalidBaseUrlError,
    RateLimitedError,
)
from ._rate_limit import Concurrency, RateClass, RateLimiter
from ._types import Download, OkResponse

__all__ = [
    "DEFAULT_BASE_URL",
    "ENV_API_KEY",
    "ENV_BASE_URL",
    "ENV_BEARER_TOKEN",
    "AsyncClient",
]

#: The production GameTorch API base URL.
DEFAULT_BASE_URL = "https://gametorch.app/api"

#: Environment variable read by :meth:`AsyncClient.from_env` for the API key.
ENV_API_KEY = "GAMETORCH_API_KEY"

#: Environment variable read by :meth:`AsyncClient.from_env` for the base URL.
ENV_BASE_URL = "GAMETORCH_BASE_URL"

#: Optional environment variable holding a Clerk session/bearer token.
ENV_BEARER_TOKEN = "GAMETORCH_TOKEN"

_RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
_MAX_BACKOFF_SECONDS = 30.0
_JITTER_SECONDS = 0.25

T = TypeVar("T", bound=BaseModel)


def _normalize_base_url(url: str) -> str:
    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise InvalidBaseUrlError(f"invalid base URL: {url!r}")
    path = parsed.path
    if not path.endswith("/"):
        path = path.rstrip("/") + "/"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def _is_retryable_status(status: int) -> bool:
    return status in _RETRYABLE_STATUSES


def _is_retryable_transport(exc: httpx.TransportError) -> bool:
    return isinstance(exc, httpx.TransportError)


def _backoff(attempt: int, base: float) -> float:
    exponential = min(base * float(1 << min(attempt, 6)), _MAX_BACKOFF_SECONDS)
    return exponential + random.random() * _JITTER_SECONDS


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(int(value.strip()))
    except (TypeError, ValueError):
        # HTTP-date form is not worth an extra dependency; fall back to backoff.
        return None


def _retry_delay(response: httpx.Response, attempt: int, base: float) -> float:
    delay = _parse_retry_after(response.headers.get("retry-after"))
    if delay is not None:
        return delay
    return _backoff(attempt, base)


def _parse_api_error(response: httpx.Response) -> ApiError:
    request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
    message: str | None = None
    try:
        body = response.json()
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            message = body["error"]
    except (json.JSONDecodeError, ValueError):
        message = None

    if message is None:
        text = response.text.strip()
        message = text or (response.reason_phrase or "unknown error")
    return ApiError(response.status_code, message, request_id)


class AsyncClient(
    CatalogMixin,
    ProjectsMixin,
    SpritesMixin,
    SoundsMixin,
    AnimationsMixin,
    ExportsMixin,
    SavedAnimationsMixin,
    LabelsMixin,
    ArtStylesMixin,
    UsageMixin,
    KeysMixin,
    AccountMixin,
):
    """An async client for the GameTorch API.

    The client is cheap to copy via :meth:`clone`; copies share the underlying
    connection pool and rate limiter, so a single client is enough for the whole
    application.

    Example::

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
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        bearer_token: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 120.0,
        connect_timeout: float | None = 15.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
        rate_limit: bool = True,
        user_agent: str | None = None,
        default_headers: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if api_key and bearer_token:
            raise ConfigError("provide either api_key or bearer_token, not both")
        if max_retries < 0:
            raise ConfigError("max_retries must be >= 0")

        self._auth_token = api_key or bearer_token
        resolved_base = base_url or os.environ.get(ENV_BASE_URL) or DEFAULT_BASE_URL
        self._base_url = _normalize_base_url(resolved_base)
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._limiter = RateLimiter(rate_limit)

        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": user_agent or f"gametorch-python/{_version()}",
        }
        if default_headers:
            headers.update(default_headers)
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        if timeout is None:
            timeout_config: httpx.Timeout | None = None
        else:
            timeout_config = httpx.Timeout(timeout, connect=connect_timeout)

        self._http = httpx.AsyncClient(
            headers=headers,
            timeout=timeout_config,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=16),
            transport=transport,
        )

    # -- Construction helpers -------------------------------------------------

    @classmethod
    def from_env(cls, **overrides: Any) -> AsyncClient:
        """Builds a client from ``GAMETORCH_API_KEY`` / ``GAMETORCH_BASE_URL``.

        A ``GAMETORCH_TOKEN`` bearer token is used when no API key is present.
        Explicit keyword arguments override the environment.
        """
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

    def clone(self) -> AsyncClient:
        """Returns a copy that shares the connection pool and rate limiter."""
        clone = object.__new__(AsyncClient)
        clone._auth_token = self._auth_token
        clone._base_url = self._base_url
        clone._max_retries = self._max_retries
        clone._retry_base_delay = self._retry_base_delay
        clone._limiter = self._limiter
        clone._http = self._http
        return clone

    # -- Introspection --------------------------------------------------------

    @property
    def base_url(self) -> str:
        """The base URL this client talks to, including the ``/api`` suffix."""
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        """Whether the client is authenticated."""
        return self._auth_token is not None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(base_url={self._base_url!r}, "
            f"authenticated={self.is_authenticated!r}, max_retries={self._max_retries!r})"
        )

    # -- Lifecycle ------------------------------------------------------------

    async def aclose(self) -> None:
        """Closes the underlying HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    # -- Dispatch (overridden by the sync client) -----------------------------

    def _dispatch(self, awaitable: Awaitable[T]) -> Any:
        """Returns the awaitable unchanged for the async client."""
        return awaitable

    # -- Request machinery ----------------------------------------------------

    def _build_request(
        self,
        method: str,
        path: str,
        params: Any = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Request:
        url = self._base_url + path.lstrip("/")
        return self._http.build_request(method, url, params=params, json=json_body, headers=headers)

    async def _send(
        self,
        method: str,
        path: str,
        *,
        rate_class: RateClass,
        route: str,
        concurrency: Concurrency = Concurrency.NONE,
        params: Any = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        attempt = 0
        while True:
            await self._limiter.acquire(rate_class, route)
            try:
                async with self._limiter.concurrency(concurrency):
                    request = self._build_request(method, path, params, json_body, headers)
                    response = await self._http.send(request)
            except httpx.TransportError as exc:
                if _is_retryable_transport(exc) and attempt < self._max_retries:
                    delay = _backoff(attempt, self._retry_base_delay)
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue
                raise HttpError(str(exc) or type(exc).__name__) from exc

            status = response.status_code
            if 200 <= status < 300:
                return response

            if _is_retryable_status(status) and attempt < self._max_retries:
                delay = _retry_delay(response, attempt, self._retry_base_delay)
                attempt += 1
                await asyncio.sleep(delay)
                continue

            if status == 429:
                raise RateLimitedError(attempt + 1)
            raise _parse_api_error(response)

    async def _send_json(
        self,
        model: type[T],
        method: str,
        path: str,
        **kwargs: Any,
    ) -> T:
        response = await self._send(method, path, **kwargs)
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise DecodeError(f"failed to decode response: {exc}") from exc
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise DecodeError(f"failed to decode response: {exc}") from exc

    async def _send_download(self, method: str, path: str, **kwargs: Any) -> Download:
        response = await self._send(method, path, **kwargs)
        content_type = response.headers.get("content-type")
        return Download(content_type=content_type, data=response.content)

    async def _send_ok(self, method: str, path: str, **kwargs: Any) -> None:
        await self._send(method, path, **kwargs)

    async def _send_ack(self, method: str, path: str, **kwargs: Any) -> OkResponse:
        return await self._send_json(OkResponse, method, path, **kwargs)


def _version() -> str:
    from ._version import __version__

    return __version__
