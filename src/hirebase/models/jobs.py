"""Job models: the typed ``Job`` document, the ``JobQuery`` filter, and the
paginated search result."""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .base import BoundModel, ResponseModel
from .common import Location, SalaryRange, YoeRange

# Filter fields the API expects as the string "true" rather than a JSON bool.
# We accept real booleans in the SDK and convert on the way out.
_STRING_BOOL_FIELDS = (
    "include_yoe",
    "include_no_salary",
    "visa",
    "include_expired",
    "hide_seen_jobs",
    "hide_recruiting_agencies",
    "filter_incomplete_jobs",
    "return_raw_description",
)


class Job(BoundModel):
    """A single job posting.

    Bound to its client so future helpers can be added without changing call
    sites. Unknown fields from the API are preserved.
    """

    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "_id"))
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    description_raw: Optional[str] = None
    requirements_summary: Optional[str] = None

    application_link: Optional[str] = None
    company_link: Optional[str] = None
    company_logo: Optional[str] = None
    job_board: Optional[str] = None
    job_board_link: Optional[str] = None

    company_slug: Optional[str] = None
    job_slug: Optional[str] = None

    job_type: Optional[Union[str, List[str]]] = None
    location_type: Optional[Union[str, List[str]]] = None
    location_raw: Optional[str] = None
    locations: Optional[List[Location]] = None

    date_posted: Optional[str] = None
    expired: Optional[bool] = None

    salary_range: Optional[SalaryRange] = None
    yoe_range: Optional[YoeRange] = None
    experience_level: Optional[str] = None
    education_level: Optional[str] = None

    job_categories: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    team: Optional[str] = None

    visa_sponsored: Optional[bool] = None
    recruiter_agency: Optional[bool] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    # Hirebase scores (0-1). Present on detailed responses.
    coolness_score: Optional[float] = None
    flexibility_score: Optional[float] = None
    compensation_value_score: Optional[float] = None
    benefits_score: Optional[float] = None
    impact_autonomy_score: Optional[float] = None
    prestige_score: Optional[float] = None
    growth_score: Optional[float] = None

    score: Optional[float] = None

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Job(title={self.job_title!r}, company={self.company_name!r})"


class JobQuery(BaseModel):
    """Typed filter for job search / export / insights.

    Every field is optional. Booleans are converted to the API's string-"true"
    convention automatically. ``locations`` is accepted as an alias for
    ``geo_locations`` for convenience.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Text
    job_titles: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    company_keywords: Optional[List[str]] = None
    company_names: Optional[Union[str, List[str]]] = Field(
        default=None, validation_alias=AliasChoices("company_names", "company_name")
    )
    company_slugs: Optional[Union[str, List[str]]] = Field(
        default=None, validation_alias=AliasChoices("company_slugs", "company_slug")
    )

    # Location
    geo_locations: Optional[List[Location]] = Field(
        default=None, validation_alias=AliasChoices("geo_locations", "locations")
    )
    location_group: Optional[str] = None
    location_types: Optional[List[str]] = None

    # Experience
    experience: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    yoe: Optional[YoeRange] = None
    include_yoe: Optional[bool] = None

    # Company
    company_types: Optional[List[str]] = None

    # Date
    date_posted: Optional[str] = None
    days_ago: Optional[int] = None
    month: Optional[str] = None

    # Salary
    salary: Optional[SalaryRange] = None
    include_no_salary: Optional[bool] = None
    currency: Optional[str] = None

    # Job type / taxonomy
    job_types: Optional[List[str]] = None
    job_category: Optional[List[str]] = None
    industry: Optional[Union[str, List[str]]] = None
    sub_industry: Optional[Union[str, List[str]]] = None
    job_board: Optional[Union[str, List[str]]] = None

    # Flags
    visa: Optional[bool] = None
    include_expired: Optional[bool] = None
    hide_recruiting_agencies: Optional[bool] = None
    filter_incomplete_jobs: Optional[bool] = None
    return_raw_description: Optional[bool] = None

    # Pagination / sorting
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page: Optional[int] = None
    limit: Optional[int] = None

    def to_payload(self) -> dict:
        """Serialize to the exact JSON body the API expects."""
        raw = self.model_dump(exclude_none=True, by_alias=False)
        for field in _STRING_BOOL_FIELDS:
            if isinstance(raw.get(field), bool):
                raw[field] = "true" if raw[field] else None
        return {k: v for k, v in raw.items() if v is not None}


def coerce_query(query: Optional[Union[JobQuery, dict]]) -> JobQuery:
    """Normalize a user-supplied query (dict or JobQuery) into a JobQuery."""
    if query is None:
        return JobQuery()
    if isinstance(query, JobQuery):
        return query
    if isinstance(query, dict):
        return JobQuery(**query)
    raise TypeError(
        f"query must be a JobQuery or dict, got {type(query).__name__}"
    )


class JobSearchResult(ResponseModel):
    """Paginated result of a job search.

    Iterating over the result iterates over its jobs.
    """

    jobs: List[Job] = Field(default_factory=list)
    total_count: int = 0
    company_count: int = 0
    page: int = 1
    limit: int = 0
    total_pages: int = 0

    def __iter__(self):  # type: ignore[override]
        return iter(self.jobs)

    def __len__(self) -> int:
        return len(self.jobs)

    def __getitem__(self, index):
        return self.jobs[index]
