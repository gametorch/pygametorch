"""Errors raised by the GameTorch SDK.

Every fallible operation raises a subclass of :class:`GametorchError`. The
:class:`ApiError` type exposes the HTTP status, the API's ``error`` message and
convenience predicates such as :meth:`ApiError.is_not_found`.
"""

from __future__ import annotations

__all__ = [
    "ApiError",
    "ConfigError",
    "DecodeError",
    "GametorchError",
    "HttpError",
    "InvalidBaseUrlError",
    "RateLimitedError",
]


class GametorchError(Exception):
    """Base class for all errors raised by the GameTorch SDK."""

    #: A short, stable label for the error kind, useful in logs.
    kind: str = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:  # pragma: no cover - inherited behaviour
        return self.message


class HttpError(GametorchError):
    """The HTTP transport failed (DNS, TLS, connection, timeout, body read)."""

    kind = "http"


class ApiError(GametorchError):
    """The API returned a non-success status.

    The API normally responds with a JSON ``{"error": ...}`` body, which is
    surfaced as :attr:`message`.
    """

    kind = "api"

    def __init__(
        self,
        status: int,
        message: str,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.request_id = request_id

    def __str__(self) -> str:
        return f"GameTorch API error ({self.status}): {self.message}"

    # Convenience predicates mirroring the Rust SDK.

    def is_not_found(self) -> bool:
        """``True`` for ``404 Not Found`` responses."""
        return self.status == 404

    def is_unauthorized(self) -> bool:
        """``True`` for ``401 Unauthorized`` responses."""
        return self.status == 401

    def is_payment_required(self) -> bool:
        """``True`` for ``402 Payment Required`` responses.

        GameTorch uses ``402`` for insufficient credits or a spending limit.
        """
        return self.status == 402

    def is_forbidden(self) -> bool:
        """``True`` for ``403 Forbidden`` responses."""
        return self.status == 403

    def is_conflict(self) -> bool:
        """``True`` for ``409 Conflict`` responses.

        Typically an idempotency ``request_id`` reused with a different body.
        """
        return self.status == 409

    def is_rate_limited(self) -> bool:
        """``True`` for ``429 Too Many Requests`` responses."""
        return self.status == 429


class RateLimitedError(GametorchError):
    """The API kept returning ``429`` after the configured number of retries."""

    kind = "rate_limited"

    def __init__(self, attempts: int) -> None:
        super().__init__(f"rate limited by GameTorch after {attempts} attempt(s)")
        self.attempts = attempts

    def is_rate_limited(self) -> bool:
        return True


class ConfigError(GametorchError):
    """The client was misconfigured, for example no credentials were supplied."""

    kind = "config"


class InvalidBaseUrlError(GametorchError):
    """The supplied base URL could not be parsed."""

    kind = "invalid_base_url"


class DecodeError(GametorchError):
    """A response could not be deserialized, or the body was not valid JSON."""

    kind = "decode"
