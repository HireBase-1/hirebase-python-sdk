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
from .models.neural import (
    NeuralSearchQuery,
    NeuralVectorQuery,
    coerce_neural_search,
    coerce_neural_vector,
    extract_job_id,
    merge_job_ids,
)
from .models.resumes import ResumeEmbedResponse, ResumeRecord
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
    # Multipart upload: ``{"file": (filename, fileobj, content_type)}``
    files: Optional[Dict[str, Any]] = None


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


def get_company_job_request(company_slug: str, job_slug: str) -> Request:
    return Request(
        "GET",
        f"/v2/hirebase/companies/{company_slug}/jobs/{job_slug}",
    )


def resolve_job_id_from_slug(client: Any, company_slug: str, job_slug: str) -> str:
    data = client._request(get_company_job_request(company_slug, job_slug))
    jobs = data.get("jobs") or []
    if not jobs:
        raise ValueError(
            f"No job found for company_slug={company_slug!r} job_slug={job_slug!r}"
        )
    return extract_job_id(jobs[0])


def prepare_neural_vector(
    client: Any,
    vector: Optional[Union[NeuralVectorQuery, dict]] = None,
    *,
    query: Optional[str] = None,
    vectors: Optional[list] = None,
    job_ids: Optional[list] = None,
    job: Optional[Union[Job, dict, str]] = None,
    jobs: Optional[list] = None,
    artifact_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    company_slug: Optional[str] = None,
    job_slug: Optional[str] = None,
    score_threshold: Optional[float] = None,
) -> NeuralVectorQuery:
    """Coerce shortcuts and resolve slug/job references into a vector spec."""
    v = coerce_neural_vector(
        vector,
        query=query,
        vectors=vectors,
        job_ids=job_ids,
        artifact_id=artifact_id,
        resume_id=resume_id,
        score_threshold=score_threshold,
    )
    v = merge_job_ids(v, job=job, jobs=jobs)
    if company_slug and job_slug:
        jid = resolve_job_id_from_slug(client, company_slug, job_slug)
        v = merge_job_ids(v, job_ids=[jid])
    elif company_slug or job_slug:
        raise ValueError("company_slug and job_slug must be provided together")
    return v


def neural_search_request(
    search: NeuralSearchQuery,
    *,
    page: Optional[int] = None,
    limit: Optional[int] = None,
) -> Request:
    lexical = search.lexical or JobQuery()
    if page is not None:
        lexical.page = page
    if limit is not None:
        lexical.limit = limit
    body = NeuralSearchQuery(
        vector=search.vector,
        lexical=lexical,
    ).to_payload()
    return Request("POST", "/v2/jobs/neural-search", json=body)


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


# ─────────────────────────────────────────────────────────────────────────
# Resumes
# ─────────────────────────────────────────────────────────────────────────


def resume_upload_request(files: Dict[str, Any]) -> Request:
    return Request("POST", "/v2/resumes/upload/", files=files)


def resume_embed_request(files: Dict[str, Any]) -> Request:
    """Enterprise: parse + embed in one call; resume is not stored."""
    return Request("POST", "/v2/resumes/embed", files=files)


def resume_get_request(resume_id: str) -> Request:
    return Request("GET", f"/v2/resumes/{resume_id}")


def resume_parse_request(resume_id: str) -> Request:
    return Request("POST", f"/v2/resumes/{resume_id}/parse")


def parse_resume_record(
    data: dict, return_type: Optional[Type]
) -> Union[ResumeRecord, dict]:
    if _want_dict(return_type):
        return data
    return ResumeRecord.model_validate(data)


def parse_resume_embed(
    data: dict, return_type: Optional[Type]
) -> Union[ResumeEmbedResponse, dict]:
    if _want_dict(return_type):
        return data
    return ResumeEmbedResponse.model_validate(data)


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
