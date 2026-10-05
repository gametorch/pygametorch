"""Tests for the error hierarchy and API error parsing."""

from __future__ import annotations

import httpx

from gametorch import ApiError, GametorchError, RateLimitedError
from gametorch._client import _parse_api_error


def test_api_error_predicates() -> None:
    assert ApiError(404, "nope").is_not_found()
    assert ApiError(401, "no").is_unauthorized()
    assert ApiError(402, "pay").is_payment_required()
    assert ApiError(403, "no").is_forbidden()
    assert ApiError(409, "dup").is_conflict()
    assert ApiError(429, "slow").is_rate_limited()
    assert not ApiError(500, "boom").is_not_found()


def test_api_error_message_and_kind() -> None:
    err = ApiError(404, "no such asset", "req-123")
    assert err.status == 404
    assert err.message == "no such asset"
    assert err.request_id == "req-123"
    assert err.kind == "api"
    assert "404" in str(err)
    assert isinstance(err, GametorchError)


def test_rate_limited_error() -> None:
    err = RateLimitedError(4)
    assert err.attempts == 4
    assert err.kind == "rate_limited"
    assert err.is_rate_limited()


def test_parse_api_error_from_json_body() -> None:
    response = httpx.Response(
        422,
        json={"error": "prompt is required"},
        headers={"x-request-id": "req-9"},
    )
    err = _parse_api_error(response)
    assert err.status == 422
    assert err.message == "prompt is required"
    assert err.request_id == "req-9"


def test_parse_api_error_from_text_body() -> None:
    response = httpx.Response(500, text="upstream exploded")
    err = _parse_api_error(response)
    assert err.message == "upstream exploded"


def test_parse_api_error_falls_back_to_reason() -> None:
    response = httpx.Response(500)
    err = _parse_api_error(response)
    assert err.message  # reason phrase or fallback
