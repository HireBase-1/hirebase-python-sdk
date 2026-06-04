"""Shared test fixtures and a transport stub.

Offline tests run everywhere. Live integration tests (test_integration.py) are
skipped unless HIREBASE_API_KEY is set.
"""

import os
import sys

import pytest

# Make ``src`` importable without installing the package.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import hirebase  # noqa: E402
from hirebase import _ops as ops  # noqa: E402


class MockTransport:
    """Records requests and returns canned responses.

    Map keys are ``(METHOD, PATH)``; values are dicts or callables taking the
    Request and returning a dict.
    """

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def add(self, method, path, response):
        self.responses[(method, path)] = response

    def handle(self, req: ops.Request):
        self.calls.append(req)
        key = (req.method, req.path)
        if key not in self.responses:
            raise AssertionError(f"No mock response registered for {key}")
        value = self.responses[key]
        return value(req) if callable(value) else value


@pytest.fixture
def mock_sync_client(monkeypatch):
    """A real sync Client with its transport stubbed out."""
    transport = MockTransport()
    client = hirebase.Client(api_key="test-key", base_url="https://api.test")
    monkeypatch.setattr(client, "_request", transport.handle)
    client.transport = transport  # type: ignore[attr-defined]
    return client


@pytest.fixture
def mock_async_client(monkeypatch):
    """A real AsyncClient with its transport stubbed with an async shim."""
    transport = MockTransport()
    client = hirebase.AsyncClient(api_key="test-key", base_url="https://api.test")

    async def _async_handle(req):
        return transport.handle(req)

    monkeypatch.setattr(client, "_request", _async_handle)
    client.transport = transport  # type: ignore[attr-defined]
    return client
