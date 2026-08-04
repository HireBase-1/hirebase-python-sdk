"""The ``usage`` resource: billing-period meter usage."""

from __future__ import annotations

from typing import Optional, Type, Union, overload

from .. import _ops as ops
from ..models.usage import MeterUsage, Meters, UsageSummary


class UsageResource:
    """Synchronous billing usage API."""

    def __init__(self, client) -> None:
        self._c = client

    @overload
    def get(self, *, meter: Meters, return_type: Optional[Type] = ...) -> MeterUsage: ...

    @overload
    def get(self, *, return_type: Optional[Type] = ...) -> UsageSummary: ...

    def get(
        self,
        *,
        meter: Optional[Meters] = None,
        return_type: Optional[Type] = None,
    ) -> Union[MeterUsage, UsageSummary, dict]:
        """Fetch usage for the current billing period.

        With ``meter=``, returns a single ``MeterUsage`` row (404-style error
        if that meter is absent). Without ``meter``, returns the full summary.
        """
        req = ops.usage_summary_request()
        data = self._c._request(req)
        summary = ops.parse_usage_summary(data, self._c, return_type)
        if meter is None:
            return summary
        return ops.parse_usage_meter(data, meter, self._c, return_type)


class AsyncUsageResource:
    """Asynchronous billing usage API."""

    def __init__(self, client) -> None:
        self._c = client

    @overload
    async def get(
        self, *, meter: Meters, return_type: Optional[Type] = ...
    ) -> MeterUsage: ...

    @overload
    async def get(self, *, return_type: Optional[Type] = ...) -> UsageSummary: ...

    async def get(
        self,
        *,
        meter: Optional[Meters] = None,
        return_type: Optional[Type] = None,
    ) -> Union[MeterUsage, UsageSummary, dict]:
        req = ops.usage_summary_request()
        data = await self._c._request(req)
        summary = ops.parse_usage_summary(data, self._c, return_type)
        if meter is None:
            return summary
        return ops.parse_usage_meter(data, meter, self._c, return_type)
