"""Company models: the typed ``Company`` document, the ``CompanyQuery`` filter
and the paginated search result."""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .base import BoundModel, ResponseModel
from .common import CompanySizeRange, Location
from .jobs import Job


class CompanyHeadquarters(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[dict] = None
    bbox: Optional[List[float]] = None


class CompanyStock(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    stock_type: Optional[str] = None
    index: Optional[str] = None
    symbol: Optional[str] = None


class CompanyFunding(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    type: Optional[str] = None
    total_rounds: Optional[int] = None
    last_funding_round: Optional[str] = None
    total_funding: Optional[float] = None


class Company(BoundModel):
    """A company profile.

    Returned by ``companies.search`` (flattened search item) and
    ``companies.get`` (full detail). When fetched via ``companies.get`` it is
    bound to the client, so ``company.insights()`` and ``company.get_jobs()``
    work directly. ``company.jobs`` holds the jobs returned alongside the
    profile (when requested).
    """

    company_slug: str
    company_name: str
    company_logo: Optional[str] = None
    company_link: Optional[str] = None
    linkedin_link: Optional[str] = None

    description_summary: Optional[str] = None
    culture_summary: Optional[str] = None
    services: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    subindustries: Optional[List[str]] = None
    size_range: Optional[CompanySizeRange] = None
    clout: Optional[float] = None
    headquarters: Optional[CompanyHeadquarters] = None
    founded: Optional[int] = None
    stock_info: Optional[CompanyStock] = None
    funding_info: Optional[CompanyFunding] = None
    type: Optional[str] = None
    is_3rd_party_agency: Optional[bool] = None
    is_recruiting_agency: Optional[bool] = None
    mean_opinion_score: Optional[float] = None
    aliases: Optional[List[str]] = None
    parent_company: Optional[str] = None
    subsidiaries: Optional[List[str]] = None

    score: Optional[float] = None

    # Populated by companies.get(..., return_jobs=True). Not part of the search
    # item shape, hence Optional and excluded when unset.
    jobs: Optional[List[Job]] = None
    # Populated by companies.get(..., return_insights=True).
    insights_data: Optional[Any] = Field(default=None, exclude=True)

    @field_validator("headquarters", mode="before")
    @classmethod
    def _coerce_hq(cls, v):
        # The API sometimes returns a bare string for legacy records.
        if v is None or isinstance(v, (dict, CompanyHeadquarters)):
            return v
        return None

    def insights(self, query=None, **kwargs):
        """Live insights for jobs at this company.

        Works on sync and async clients (returns a coroutine for async).
        """
        client = self._require_client()
        return client.companies.insights(self.company_slug, query=query, **kwargs)

    def get_jobs(self, **kwargs):
        """Fetch jobs for this company (paginated)."""
        client = self._require_client()
        return client.companies.jobs(self.company_slug, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Company(slug={self.company_slug!r}, name={self.company_name!r})"


class CompanyQuery(BaseModel):
    """Typed filter for company search. All fields optional, extras allowed."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    company_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    query: Optional[str] = None
    company_link: Optional[str] = None
    linkedin_link: Optional[str] = None

    industries: Optional[List[str]] = None
    subindustries: Optional[List[str]] = None
    company_types: Optional[List[str]] = Field(
        default=None, validation_alias=AliasChoices("company_types", "company_sizes")
    )
    types: Optional[List[str]] = None

    hq_geolocations: Optional[List[Location]] = None
    parent_company: Optional[str] = None
    is_3rd_party_agency: Optional[bool] = None
    is_recruiting_agency: Optional[bool] = None
    hide_recruiter_agencies: Optional[bool] = None

    funding_types: Optional[List[str]] = None

    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page: Optional[int] = None
    limit: Optional[int] = None

    def to_payload(self) -> dict:
        return self.model_dump(exclude_none=True, by_alias=False)


def coerce_company_query(
    query: Optional[Union[CompanyQuery, dict]]
) -> CompanyQuery:
    if query is None:
        return CompanyQuery()
    if isinstance(query, CompanyQuery):
        return query
    if isinstance(query, dict):
        return CompanyQuery(**query)
    raise TypeError(
        f"query must be a CompanyQuery or dict, got {type(query).__name__}"
    )


class CompanySearchResult(ResponseModel):
    """Paginated company search result. Iterates over companies."""

    companies: List[Company] = Field(default_factory=list)
    total_count: int = 0
    page: int = 1
    limit: int = 0
    total_pages: int = 0

    def __iter__(self):  # type: ignore[override]
        return iter(self.companies)

    def __len__(self) -> int:
        return len(self.companies)

    def __getitem__(self, index):
        return self.companies[index]
