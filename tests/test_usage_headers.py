"""``Hirebase-Usage-*`` header parsing, ``client.last_usage`` and the
quota-vs-rate-limit 429 split (no network)."""
from types import SimpleNamespace

import pytest

import hirebase
from hirebase.client import _handle_response
from hirebase.exceptions import QuotaExceededError, RateLimitError, error_from_response
from hirebase.models.usage import UsageSnapshot

QUOTA_HEADERS = {
    "Hirebase-Usage-Feature": "jobs_api",
    "Hirebase-Usage-Meter": "m_jobs_api_calls",
    "Hirebase-Usage-Unit": "jobs",
    "Hirebase-Usage-Included-Limit": "500",
    "Hirebase-Usage-Included-Used": "500",
    "Hirebase-Usage-Included-Remaining": "0",
    "Hirebase-Usage-Overage-Used": "3",
    "Hirebase-Usage-Overage-Mode": "block",
    "Hirebase-Usage-Total-Used": "503",
    "Hirebase-Usage-Period-Start": "2026-09-01T00:00:00Z",
    "Hirebase-Usage-Period-End": "2026-09-30T23:59:59Z",
    "X-Billing-Code": "limit_exceeded",
}


def test_snapshot_from_headers_is_case_insensitive():
    snap = UsageSnapshot.from_headers({k.lower(): v for k, v in QUOTA_HEADERS.items()})
    assert snap is not None
    assert snap.meter == "m_jobs_api_calls"
    assert snap.included_limit == 500
    assert snap.included_remaining == 0
    assert snap.overage_used == 3
    assert snap.total_used == 503
    assert snap.period_end == "2026-09-30T23:59:59Z"
    assert snap.is_blocked and not snap.is_meter_mode


def test_snapshot_absent_without_usage_headers():
    assert UsageSnapshot.from_headers({}) is None
    assert UsageSnapshot.from_headers(None) is None
    assert UsageSnapshot.from_headers({"Content-Type": "application/json"}) is None


def test_snapshot_tolerates_bad_numbers():
    snap = UsageSnapshot.from_headers({"Hirebase-Usage-Meter": "m_jobs_api_calls", "Hirebase-Usage-Total-Used": "n/a"})
    assert snap is not None and snap.total_used is None and snap.overage_used == 0


def test_quota_429_maps_to_quota_exceeded_error():
    body = {"detail": "You've reached your plan's included usage of 500 for this period."}
    err = error_from_response(429, body, QUOTA_HEADERS)
    assert isinstance(err, QuotaExceededError)
    assert isinstance(err, RateLimitError)  # backwards compatible
    assert err.usage is not None and err.usage.included_remaining == 0
    assert err.retry_after is None
    assert "included usage of 500" in str(err)


def test_rate_limit_429_stays_rate_limit_error_with_retry_after():
    headers = {"Retry-After": "42", "X-RateLimit-Limit": "100", "X-RateLimit-Remaining": "0"}
    err = error_from_response(429, {"detail": "Rate limit exceeded"}, headers)
    assert type(err) is RateLimitError
    assert err.retry_after == 42


def test_429_without_headers_is_plain_rate_limit_error():
    err = error_from_response(429, {"detail": "slow down"})
    assert type(err) is RateLimitError
    assert err.retry_after is None and err.usage is None


def test_handle_response_passes_headers_to_error():
    resp = SimpleNamespace(headers=QUOTA_HEADERS)
    with pytest.raises(QuotaExceededError) as info:
        _handle_response(429, b'{"detail": "cap"}', resp)
    assert info.value.usage.is_blocked


def test_client_last_usage_updates_per_call(monkeypatch):
    client = hirebase.Client(api_key="test-key", base_url="https://api.test")
    ok_headers = {**QUOTA_HEADERS, "Hirebase-Usage-Included-Used": "12", "Hirebase-Usage-Included-Remaining": "488",
                  "Hirebase-Usage-Overage-Used": "0", "Hirebase-Usage-Total-Used": "12"}
    ok_headers.pop("X-Billing-Code")
    responses = [
        SimpleNamespace(status_code=200, content=b'{"jobs": [], "total_count": 0}', headers=ok_headers),
        SimpleNamespace(status_code=429, content=b'{"detail": "cap"}', headers=QUOTA_HEADERS),
        SimpleNamespace(status_code=200, content=b'{"ok": true}', headers={"Content-Type": "application/json"}),
    ]
    monkeypatch.setattr(client._session, "request", lambda **kwargs: responses.pop(0))

    assert client.last_usage is None
    client.jobs.search({"job_titles": ["SWE"]}, return_type=dict)
    assert client.last_usage.included_remaining == 488 and not client.last_usage.is_blocked

    with pytest.raises(QuotaExceededError):
        client.jobs.search({"job_titles": ["SWE"]})
    assert client.last_usage.is_blocked and client.last_usage.total_used == 503

    client.jobs.search({"job_titles": ["SWE"]}, return_type=dict)
    assert client.last_usage is None  # un-metered response clears it


def test_async_client_last_usage(monkeypatch):
    import asyncio

    client = hirebase.AsyncClient(api_key="test-key", base_url="https://api.test")

    async def fake_request(*args, **kwargs):
        return SimpleNamespace(status_code=200, content=b'{"jobs": []}', headers=QUOTA_HEADERS)

    monkeypatch.setattr(client._http, "request", fake_request)

    async def run():
        await client.jobs.search({"job_titles": ["SWE"]}, return_type=dict)
        return client.last_usage

    snap = asyncio.run(run())
    assert snap is not None and snap.total_used == 503


def test_exports():
    assert hirebase.QuotaExceededError is QuotaExceededError
    assert hirebase.UsageSnapshot is UsageSnapshot
