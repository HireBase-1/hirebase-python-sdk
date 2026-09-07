"""Primitive value objects shared across jobs and companies."""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict


class _Value(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Location(_Value):
    """A geographic location used in both filters and responses.

    On *search / insights* filters, send ``city`` / ``region`` / ``country``
    only. The API geocodes those fields. ``coordinates`` on the request must
    be a GeoJSON dict if present; a ``[lon, lat]`` list returns HTTP 422.
    Use ``JobQuery.geofilter_params`` for the radius circle.
    """

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Union[dict, List[float]]] = None
    bbox: Optional[List[float]] = None

    def __str__(self) -> str:
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ", ".join(parts) if parts else "Unknown"


class GeoFilterParams(_Value):
    """Circle / phrase / bbox mode for ``geo_locations``.

    ``mode="auto"`` (the API default) uses a ``geoWithin`` circle when a city
    is present (after server-side geocode) and phrase-match otherwise.
    App default radius is 25 miles; pass 35 for a typical metro labor market.
    """

    mode: Literal["auto", "weak", "strict", "box"] = "auto"
    radius: float = 25.0
    unit: Literal["mi", "km", "degrees"] = "mi"


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


class FloatRange(_Value):
    """Inclusive numeric range used by company filters (e.g. MOS)."""

    min: Optional[float] = None
    max: Optional[float] = None
