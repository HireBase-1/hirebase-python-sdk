"""Billing usage models — mirrors ``GET /v2/billing/usage/summary``."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union

from pydantic import BaseModel

from .base import BoundModel, ResponseModel


class Meters(str, Enum):
    """Stripe meter event names for API usage."""

    JOBS_API = "m_jobs_api_calls"
    COMPANY_API = "m_company_api_calls"
    VECTOR_API = "m_vector_api_calls"
    EXPORTS = "m_exports"
    INSIGHTS = "m_insights_calls"
    SALARY_BENCHMARKS = "m_salary_benchmarks"


class MeterUsage(BoundModel):
    """Usage for a single meter in the current billing period."""

    event_name: str
    display_name: str
    used: int
    included: Optional[int] = None
    remaining: Optional[int] = None
    overage_used: int = 0
    period: Optional[str] = "month"
    overage_mode: Optional[str] = None
    overage_unit: Optional[int] = None
    overage_cents_per_unit: Optional[int] = None
    estimated_overage_cents: int = 0
    overage_currency: str = "usd"


class UsageSummary(BoundModel):
    """Current billing-period usage across all meters."""

    billing_source: str = "stripe_v2"
    stripe_customer_id: Optional[str] = None
    plan_lookup_keys: List[str] = []
    subscription_status: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    meters: List[MeterUsage] = []

    def meter(self, meter: Union[Meters, str]) -> Optional[MeterUsage]:
        """Return one meter row by enum or event name."""
        key = meter.value if isinstance(meter, Meters) else meter
        for row in self.meters:
            if row.event_name == key:
                return row
        return None


_USAGE_PREFIX = "hirebase-usage-"


def _to_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class UsageSnapshot(BaseModel):
    """Quota state stamped on every metered response (``Hirebase-Usage-*``).

    Read it from ``meta.usage`` after calling any resource method with
    ``return_meta=True``, or from ``QuotaExceededError.usage`` when a call is
    refused at the cap. It lets you stay under quota without polling
    ``client.usage.get()``.
    """

    meter: Optional[str] = None
    feature: Optional[str] = None
    unit: Optional[str] = None
    included_limit: Optional[int] = None
    included_used: Optional[int] = None
    included_remaining: Optional[int] = None
    overage_used: int = 0
    overage_mode: Optional[str] = None
    total_used: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    billing_code: Optional[str] = None
    retry_after: Optional[int] = None

    @property
    def is_blocked(self) -> bool:
        """True when the API refused the call because the cap was reached."""
        return self.billing_code == "limit_exceeded"

    @property
    def is_meter_mode(self) -> bool:
        """True when usage past the allowance is billed instead of refused."""
        return self.overage_mode == "meter"

    @classmethod
    def from_headers(cls, headers: Optional[Mapping[str, Any]]) -> Optional["UsageSnapshot"]:
        """Build a snapshot from response headers; None if no usage headers."""
        if not headers:
            return None
        lowered = {str(k).lower(): v for k, v in headers.items()}
        usage = {k[len(_USAGE_PREFIX):]: v for k, v in lowered.items() if k.startswith(_USAGE_PREFIX)}
        billing_code = lowered.get("x-billing-code")
        if not usage and billing_code is None:
            return None
        return cls(
            meter=usage.get("meter"),
            feature=usage.get("feature"),
            unit=usage.get("unit"),
            included_limit=_to_int(usage.get("included-limit")),
            included_used=_to_int(usage.get("included-used")),
            included_remaining=_to_int(usage.get("included-remaining")),
            overage_used=_to_int(usage.get("overage-used")) or 0,
            overage_mode=usage.get("overage-mode"),
            total_used=_to_int(usage.get("total-used")),
            period_start=usage.get("period-start"),
            period_end=usage.get("period-end"),
            billing_code=billing_code,
            retry_after=_to_int(lowered.get("retry-after")),
        )


class ResponseMeta(BaseModel):
    """Transport-level metadata for one API call.

    Returned alongside the parsed body when a resource method is called with
    ``return_meta=True``::

        jobs, meta = client.jobs.search(query, limit=50, return_meta=True)
        if meta.usage and meta.usage.included_remaining is not None:
            print("jobs left this period:", meta.usage.included_remaining)

    ``usage`` is ``None`` on un-metered endpoints. ``headers`` keys are
    lower-cased.
    """

    status_code: int
    headers: Dict[str, str]
    usage: Optional[UsageSnapshot] = None

    @property
    def request_id(self) -> Optional[str]:
        """The server's ``X-Request-Id`` when present (handy for support)."""
        return self.headers.get("x-request-id")

    @classmethod
    def from_response(cls, resp: Any) -> "ResponseMeta":
        """Build from a ``requests``/``httpx`` response (or any look-alike)."""
        raw = getattr(resp, "headers", None) or {}
        headers = {str(k).lower(): str(v) for k, v in raw.items()}
        return cls(
            status_code=int(getattr(resp, "status_code", 0) or 0),
            headers=headers,
            usage=UsageSnapshot.from_headers(headers),
        )
