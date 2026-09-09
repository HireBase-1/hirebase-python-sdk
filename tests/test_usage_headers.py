"""``Hirebase-Usage-*`` header parsing, per-call ``return_meta=True`` and the
quota-vs-rate-limit 429 split (no network)."""
from types import SimpleNamespace

import pytest

import hirebase
from hirebase.client import _handle_response
from hirebase.exceptions import QuotaExceededError, RateLimitError, error_from_response
from hirebase.models.usage import ResponseMeta, UsageSnapshot

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

OK_HEADERS = {
    **QUOTA_HEADERS,
    "Hirebase-Usage-Included-Used": "12",
    "Hirebase-Usage-Included-Remaining": "488",
    "Hirebase-Usage-Overage-Used": "0",
    "Hirebase-Usage-Total-Used": "12",
    "X-Request-Id": "req_abc123",
}
OK_HEADERS.pop("X-Billing-Code")


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


def test_response_meta_from_response_lowercases_headers_and_parses_usage():
    meta = ResponseMeta.from_response(SimpleNamespace(status_code=200, headers=OK_HEADERS))
    assert meta.status_code == 200
    assert meta.request_id == "req_abc123"
    assert meta.headers["hirebase-usage-meter"] == "m_jobs_api_calls"
    assert meta.usage is not None and meta.usage.included_remaining == 488


def test_response_meta_without_usage_headers():
    meta = ResponseMeta.from_response(SimpleNamespace(status_code=200, headers={"Content-Type": "application/json"}))
    assert meta.usage is None and meta.request_id is None


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


def _sync_client_with_responses(monkeypatch, responses):
    client = hirebase.Client(api_key="test-key", base_url="https://api.test")
    monkeypatch.setattr(client._session, "request", lambda **kwargs: responses.pop(0))
    return client


def test_return_meta_gives_per_call_usage(monkeypatch):
    responses = [
        SimpleNamespace(status_code=200, content=b'{"jobs": [], "total_count": 0}', headers=OK_HEADERS),
        SimpleNamespace(status_code=429, content=b'{"detail": "cap"}', headers=QUOTA_HEADERS),
        SimpleNamespace(status_code=200, content=b'{"ok": true}', headers={"Content-Type": "application/json"}),
    ]
    client = _sync_client_with_responses(monkeypatch, responses)

    result, meta = client.jobs.search({"job_titles": ["SWE"]}, return_type=dict, return_meta=True)
    assert result == {"jobs": [], "total_count": 0}
    assert isinstance(meta, ResponseMeta)
    assert meta.status_code == 200 and meta.request_id == "req_abc123"
    assert meta.usage.included_remaining == 488 and not meta.usage.is_blocked

    # A refused call still raises; the snapshot rides on the error.
    with pytest.raises(QuotaExceededError) as info:
        client.jobs.search({"job_titles": ["SWE"]}, return_meta=True)
    assert info.value.usage.is_blocked and info.value.usage.total_used == 503

    # Un-metered response: meta is present, usage is None.
    _, meta2 = client.jobs.search({"job_titles": ["SWE"]}, return_type=dict, return_meta=True)
    assert meta2.usage is None


def test_default_return_shape_is_unchanged(monkeypatch):
    responses = [
        SimpleNamespace(status_code=200, content=b'{"jobs": [], "total_count": 0}', headers=OK_HEADERS),
        SimpleNamespace(status_code=200, content=b'{"cost": 7}', headers=OK_HEADERS),
    ]
    client = _sync_client_with_responses(monkeypatch, responses)
    assert client.jobs.search({"job_titles": ["SWE"]}, return_type=dict) == {"jobs": [], "total_count": 0}
    assert client.jobs.estimate({"job_titles": ["SWE"]}) == 7


def test_return_meta_on_other_metered_methods(monkeypatch):
    responses = [
        SimpleNamespace(status_code=200, content=b'{"cost": 7}', headers=OK_HEADERS),
        SimpleNamespace(status_code=200, content=b'{"companies": [], "total_count": 0}', headers=OK_HEADERS),
    ]
    client = _sync_client_with_responses(monkeypatch, responses)
    cost, meta = client.jobs.estimate({"job_titles": ["SWE"]}, return_meta=True)
    assert cost == 7 and meta.usage.included_used == 12
    companies, meta2 = client.companies.search({"industries": ["Software"]}, return_type=dict, return_meta=True)
    assert companies["companies"] == [] and meta2.status_code == 200


def test_client_no_longer_keeps_last_usage_state():
    client = hirebase.Client(api_key="test-key", base_url="https://api.test")
    assert not hasattr(client, "last_usage")
    aclient = hirebase.AsyncClient(api_key="test-key", base_url="https://api.test")
    assert not hasattr(aclient, "last_usage")


def test_mock_transport_default_path_still_works(mock_sync_client):
    """Tests that stub ``_request`` keep working for the default (no-meta) path."""
    mock_sync_client.transport.add("POST", "/v2/jobs/search", {"jobs": [], "total_count": 0})
    assert mock_sync_client.jobs.search({"job_titles": ["SWE"]}, return_type=dict) == {"jobs": [], "total_count": 0}


def test_async_return_meta(monkeypatch):
    import asyncio

    client = hirebase.AsyncClient(api_key="test-key", base_url="https://api.test")

    async def fake_request(*args, **kwargs):
        return SimpleNamespace(status_code=200, content=b'{"jobs": []}', headers=OK_HEADERS)

    monkeypatch.setattr(client._http, "request", fake_request)

    async def run():
        plain = await client.jobs.search({"job_titles": ["SWE"]}, return_type=dict)
        result, meta = await client.jobs.search({"job_titles": ["SWE"]}, return_type=dict, return_meta=True)
        return plain, result, meta

    plain, result, meta = asyncio.run(run())
    assert plain == {"jobs": []} and result == {"jobs": []}
    assert meta.usage is not None and meta.usage.total_used == 12


def test_exports():
    assert hirebase.QuotaExceededError is QuotaExceededError
    assert hirebase.UsageSnapshot is UsageSnapshot
    assert hirebase.ResponseMeta is ResponseMeta
