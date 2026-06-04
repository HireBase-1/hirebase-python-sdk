"""Pure request-building and response-parsing logic.

This module contains *no* I/O. Each public operation is expressed as:

* a ``*_request(...) -> Request`` function that returns the HTTP spec, and
* a ``parse_*(data, client, return_type) -> ...`` function that turns the
  decoded JSON into typed models.

Keeping transport out of here means the sync and async resources share one
implementation, and the eventual JavaScript SDK can mirror this file almost
line-for-line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, Union

from .models.companies import (
    Company,
    CompanyQuery,
    CompanySearchResult,
    coerce_company_query,
)
from .models.insights import JobInsights
from .models.jobs import Job, JobQuery, JobSearchResult, coerce_query
from .models.tasks import Task

# Sentinel meaning "return typed models" (the default).
TYPED = None


@dataclass
class Request:
    """An HTTP request specification, independent of any transport."""

    method: str
    path: str
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = field(default=None)


def _want_dict(return_type: Optional[Type]) -> bool:
    return return_type is dict


# ─────────────────────────────────────────────────────────────────────────
# Jobs
# ─────────────────────────────────────────────────────────────────────────


def search_jobs_request(
    query: Optional[Union[JobQuery, dict]],
    page: Optional[int] = None,
    limit: Optional[int] = None,
) -> Request:
    q = coerce_query(query)
    if page is not None:
        q.page = page
    if limit is not None:
        q.limit = limit
    return Request("POST", "/v2/jobs/search", json=q.to_payload())


def parse_job_search(
    data: dict, client: Any, return_type: Optional[Type]
) -> Union[JobSearchResult, dict]:
    if _want_dict(return_type):
        return data
    result = JobSearchResult.model_validate(data)
    for job in result.jobs:
        job._bind(client)
    return result


def get_job_request(job_id: str) -> Request:
    return Request("GET", f"/v2/jobs/{job_id}")


def parse_job(data: dict, client: Any, return_type: Optional[Type]) -> Union[Job, dict]:
    if _want_dict(return_type):
        return data
    return Job.model_validate(data)._bind(client)


def export_jobs_request(
    query: Optional[Union[JobQuery, dict]], format: str = "json"
) -> Request:
    if format not in ("json", "csv"):
        raise ValueError("format must be 'json' or 'csv'")
    q = coerce_query(query)
    return Request(
        "POST",
        "/v2/jobs/export",
        json={"search": q.to_payload(), "format": format},
    )


def insights_request(
    query: Optional[Union[JobQuery, dict]],
    path: str = "/v2/jobs/insights",
) -> Request:
    q = coerce_query(query)
    return Request("POST", path, json=q.to_payload())


def parse_insights(
    data: dict, client: Any, return_type: Optional[Type]
) -> Union[JobInsights, dict]:
    if _want_dict(return_type):
        return data
    return JobInsights.model_validate(data)


# ─────────────────────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────────────────────


def get_task_request(task_id: str) -> Request:
    return Request("GET", f"/v2/tasks/{task_id}")


def parse_task(data: dict, client: Any, return_type: Optional[Type]) -> Union[Task, dict]:
    if _want_dict(return_type):
        return data
    return Task.model_validate(data)._bind(client)


def task_id_of(task: Union[Task, dict, str]) -> str:
    if isinstance(task, str):
        return task
    if isinstance(task, Task):
        return task.id
    if isinstance(task, dict):
        tid = task.get("id")
        if tid:
            return str(tid)
    raise TypeError("Expected a Task, task dict, or task id string.")


# ─────────────────────────────────────────────────────────────────────────
# Companies
# ─────────────────────────────────────────────────────────────────────────


def search_companies_request(
    query: Optional[Union[CompanyQuery, dict]],
    page: Optional[int] = None,
    limit: Optional[int] = None,
) -> Request:
    q = coerce_company_query(query)
    if page is not None:
        q.page = page
    if limit is not None:
        q.limit = limit
    return Request(
        "POST", "/v2/hirebase/companies/search", json=q.to_payload()
    )


def parse_company_search(
    data: dict, client: Any, return_type: Optional[Type]
) -> Union[CompanySearchResult, dict]:
    if _want_dict(return_type):
        return data
    result = CompanySearchResult.model_validate(data)
    for company in result.companies:
        company._bind(client)
    return result


def get_company_request(slug: str) -> Request:
    return Request("GET", f"/v2/hirebase/companies/{slug}")


def parse_company_detail(
    data: dict,
    client: Any,
    return_type: Optional[Type],
    return_jobs: bool = True,
) -> Union[Company, dict]:
    """Parse a ``{company, jobs}`` detail response into a bound Company."""
    if _want_dict(return_type):
        if not return_jobs:
            data = {**data, "jobs": None}
        return data

    company_payload = dict(data.get("company") or {})
    if return_jobs:
        company_payload["jobs"] = data.get("jobs") or []
    company = Company.model_validate(company_payload)._bind(client)
    if company.jobs:
        for job in company.jobs:
            job._bind(client)
    return company


def company_jobs_request(
    slug: str,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    job_board: Optional[str] = None,
    job_category: Optional[str] = None,
) -> Request:
    params: Dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    if sort_by is not None:
        params["sort_by"] = sort_by
    if sort_order is not None:
        params["sort_order"] = sort_order
    if job_board is not None:
        params["job_board"] = job_board
    if job_category is not None:
        params["job_category"] = job_category
    return Request(
        "GET", f"/v2/hirebase/companies/{slug}/jobs", params=params or None
    )


def parse_company_jobs(
    data: dict, client: Any, return_type: Optional[Type]
) -> Union[JobSearchResult, dict]:
    if _want_dict(return_type):
        return data
    # The company-jobs endpoint omits company_count; default to 0.
    payload = {"company_count": 0, **data}
    result = JobSearchResult.model_validate(payload)
    for job in result.jobs:
        job._bind(client)
    return result


def company_insights_request(
    slug: str, query: Optional[Union[JobQuery, dict]]
) -> Request:
    q = coerce_query(query)
    return Request(
        "POST",
        f"/v2/hirebase/companies/{slug}/insights",
        json=q.to_payload(),
    )


def company_slug_of(company: Union[Company, dict, str]) -> str:
    if isinstance(company, str):
        return company
    if isinstance(company, Company):
        return company.company_slug
    if isinstance(company, dict):
        slug = company.get("company_slug")
        if slug:
            return str(slug)
    raise TypeError("Expected a Company, company dict, or slug string.")
