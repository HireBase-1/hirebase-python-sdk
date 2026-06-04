"""Primitive value objects shared across jobs and companies."""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict


class _Value(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Location(_Value):
    """A geographic location used in both filters and responses."""

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Union[dict, List[float]]] = None
    bbox: Optional[List[float]] = None

    def __str__(self) -> str:
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ", ".join(parts) if parts else "Unknown"


class SalaryRange(_Value):
    """A salary band. Also used as a search filter (min/max)."""

    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None


class YoeRange(_Value):
    """Years-of-experience range. Also used as a search filter."""

    min: Optional[float] = None
    max: Optional[float] = None


class CompanySizeRange(_Value):
    min: Optional[int] = None
    max: Optional[int] = None
