"""Clients retry a 503 neural_search_warming_up until the model is warm."""

import asyncio
import json

import pytest

import hirebase
from hirebase import _ops as ops
from hirebase.exceptions import (
    ModelWarmingUpError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    error_from_response,
)

WARMING = {
    "detail": "Neural Search is starting up. Retry in about 30 seconds.",
    "code": "neural_search_warming_up",
    "retry_after": 30,
}
RESULT = {"jobs": [], "total_count": 0, "page": 1, "limit": 10, "total_pages": 0}


class FakeResponse:
    def __init__(self, status_code, body, headers=None):
        self.status_code = status_code
        self.content = json.dumps(body).encode()
        self.headers = headers or {}


def _script(*responses):
    """Return a fake transport that plays ``responses`` in order."""
    calls = []

    def send(*args, **kwargs):
        calls.append(kwargs.get("url") or (args[1] if len(args) > 1 else None))
        return responses[len(calls) - 1]

    return send, calls


def _warming():
    return FakeResponse(429, WARMING, {"Retry-After": "30"})


REQ = ops.Request("POST", "/v2/jobs/neural-search", json={"vector": {"query": "nurse"}})


def test_warming_429_maps_to_model_warming_up_error():
    err = error_from_response(429, WARMING, {"Retry-After": "30"})
    assert isinstance(err, ModelWarmingUpError)
    assert isinstance(err, RateLimitError)  # existing `except RateLimitError` still works
    assert not isinstance(err, QuotaExceededError)
    assert err.retry_after == 30


def test_plain_429_and_503_are_not_warming():
    assert type(error_from_response(429, {"detail": "Rate limit exceeded"})) is RateLimitError
    assert type(error_from_response(503, {"detail": "down"})) is ServerError


def test_sync_client_retries_until_warm(monkeypatch):
    sleeps = []
    monkeypatch.setattr("hirebase.client.time.sleep", sleeps.append)
    client = hirebase.Client(api_key="k", base_url="https://api.test")
    send, calls = _script(_warming(), _warming(), FakeResponse(200, RESULT))
    monkeypatch.setattr(client._session, "request", send)

    assert client._request(REQ) == RESULT
    assert len(calls) == 3
    assert sleeps == [30.0, 30.0]


def test_sync_client_gives_up_after_warmup_wait(monkeypatch):
    monkeypatch.setattr("hirebase.client.time.sleep", lambda s: None)
    client = hirebase.Client(api_key="k", base_url="https://api.test", warmup_wait=0)
    send, calls = _script(_warming())
    monkeypatch.setattr(client._session, "request", send)

    with pytest.raises(ModelWarmingUpError):
        client._request(REQ)
    assert len(calls) == 1


def test_async_client_retries_until_warm(monkeypatch):
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr("hirebase.client.asyncio.sleep", fake_sleep)
    client = hirebase.AsyncClient(api_key="k", base_url="https://api.test")
    send, calls = _script(_warming(), FakeResponse(200, RESULT))

    async def fake_request(*args, **kwargs):
        return send(*args, **kwargs)

    monkeypatch.setattr(client._http, "request", fake_request)

    async def run():
        try:
            return await client._request(REQ)
        finally:
            await client.aclose()

    assert asyncio.run(run()) == RESULT
    assert len(calls) == 2
    assert sleeps == [30.0]
