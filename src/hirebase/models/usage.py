"""Billing usage models — mirrors ``GET /v2/billing/usage/summary``."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from .base import BoundModel, ResponseModel


class Meters(str, Enum):
    """Stripe meter event names for API usage."""

    JOBS_API = "m_jobs_api_calls"
    COMPANY_API = "m_company_api_calls"
    VECTOR_API = "m_vector_api_calls"
    EXPORTS = "m_exports"
    INSIGHTS = "m_insights_calls"


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
