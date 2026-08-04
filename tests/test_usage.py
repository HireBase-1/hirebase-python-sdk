"""Tests for the usage resource."""

import pytest

from hirebase.exceptions import NotFoundError
from hirebase.models.usage import MeterUsage, Meters, UsageSummary


USAGE_SUMMARY = {
    "billing_source": "stripe_v2",
    "stripe_customer_id": "cus_123",
    "plan_lookup_keys": ["plan_starter"],
    "subscription_status": "active",
    "period_start": "2026-06-01T00:00:00Z",
    "period_end": "2026-07-01T00:00:00Z",
    "meters": [
        {
            "event_name": "m_jobs_api_calls",
            "display_name": "Job Search API calls",
            "used": 42,
            "included": 25000,
            "remaining": 24958,
            "overage_used": 0,
            "estimated_overage_cents": 0,
        },
        {
            "event_name": "m_company_api_calls",
            "display_name": "Company Search API calls",
            "used": 0,
            "included": 10000,
            "remaining": 10000,
            "overage_used": 0,
            "estimated_overage_cents": 0,
        },
    ],
}


def test_usage_get_summary(mock_sync_client):
    c = mock_sync_client
    c.transport.add("GET", "/v2/billing/usage/summary", USAGE_SUMMARY)
    summary = c.usage.get()
    assert isinstance(summary, UsageSummary)
    assert summary.billing_source == "stripe_v2"
    assert summary.plan_lookup_keys == ["plan_starter"]
    assert len(summary.meters) == 2
    assert summary.meter(Meters.JOBS_API).used == 42


def test_usage_get_single_meter(mock_sync_client):
    c = mock_sync_client
    c.transport.add("GET", "/v2/billing/usage/summary", USAGE_SUMMARY)
    jobs = c.usage.get(meter=Meters.JOBS_API)
    assert isinstance(jobs, MeterUsage)
    assert jobs.event_name == "m_jobs_api_calls"
    assert jobs.used == 42


def test_usage_get_missing_meter_raises(mock_sync_client):
    c = mock_sync_client
    c.transport.add("GET", "/v2/billing/usage/summary", USAGE_SUMMARY)
    with pytest.raises(NotFoundError):
        c.usage.get(meter=Meters.VECTOR_API)


@pytest.mark.asyncio
async def test_usage_get_async(mock_async_client):
    c = mock_async_client
    c.transport.add("GET", "/v2/billing/usage/summary", USAGE_SUMMARY)
    summary = await c.usage.get()
    assert isinstance(summary, UsageSummary)
    row = await c.usage.get(meter=Meters.JOBS_API)
    assert row.used == 42
