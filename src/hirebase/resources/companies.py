"""The ``companies`` resource: search, get, jobs and insights."""

from __future__ import annotations

from typing import Optional, Type, Union

from .. import _ops as ops
from ..models.companies import Company, CompanyQuery, CompanySearchResult
from ..models.insights import JobInsights
from ..models.jobs import JobQuery, JobSearchResult

CompanyQueryType = Optional[Union[CompanyQuery, dict]]
JobQueryType = Optional[Union[JobQuery, dict]]
CompanyRef = Union[Company, dict, str]


class CompaniesResource:
    """Synchronous companies API."""

    def __init__(self, client) -> None:
        self._c = client

    def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
    ) -> Union[CompanySearchResult, dict]:
        req = ops.search_companies_request(query, page=page, limit=limit)
        data = self._c._request(req)
        return ops.parse_company_search(data, self._c, return_type)

    def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
    ) -> Union[Company, dict]:
        """Fetch a company by slug.

        Set ``return_insights=True`` to also fetch live insights (an extra
        request); they are attached at ``company.insights_data`` (typed) or
        under the ``insights`` key (dict).
        """
        req = ops.get_company_request(slug)
        data = self._c._request(req)
        company = ops.parse_company_detail(
            data, self._c, return_type, return_jobs=return_jobs
        )
        if return_insights:
            insights = self.insights(slug, return_type=return_type)
            if isinstance(company, dict):
                company["insights"] = (
                    insights if isinstance(insights, dict) else insights.model_dump()
                )
            else:
                company.insights_data = insights
        return company

    def jobs(
        self,
        company: CompanyRef,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        job_board: Optional[str] = None,
        job_category: Optional[str] = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobSearchResult, dict]:
        """Paginated jobs for a company."""
        slug = ops.company_slug_of(company)
        req = ops.company_jobs_request(
            slug,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            job_board=job_board,
            job_category=job_category,
        )
        data = self._c._request(req)
        return ops.parse_company_jobs(data, self._c, return_type)

    def insights(
        self,
        company: CompanyRef,
        *,
        query: JobQueryType = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobInsights, dict]:
        """Live insights for jobs at a company."""
        slug = ops.company_slug_of(company)
        req = ops.company_insights_request(slug, query)
        data = self._c._request(req)
        return ops.parse_insights(data, self._c, return_type)


class AsyncCompaniesResource:
    """Asynchronous companies API."""

    def __init__(self, client) -> None:
        self._c = client

    async def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
    ) -> Union[CompanySearchResult, dict]:
        req = ops.search_companies_request(query, page=page, limit=limit)
        data = await self._c._request(req)
        return ops.parse_company_search(data, self._c, return_type)

    async def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
    ) -> Union[Company, dict]:
        req = ops.get_company_request(slug)
        data = await self._c._request(req)
        company = ops.parse_company_detail(
            data, self._c, return_type, return_jobs=return_jobs
        )
        if return_insights:
            insights = await self.insights(slug, return_type=return_type)
            if isinstance(company, dict):
                company["insights"] = (
                    insights if isinstance(insights, dict) else insights.model_dump()
                )
            else:
                company.insights_data = insights
        return company

    async def jobs(
        self,
        company: CompanyRef,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        job_board: Optional[str] = None,
        job_category: Optional[str] = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobSearchResult, dict]:
        slug = ops.company_slug_of(company)
        req = ops.company_jobs_request(
            slug,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            job_board=job_board,
            job_category=job_category,
        )
        data = await self._c._request(req)
        return ops.parse_company_jobs(data, self._c, return_type)

    async def insights(
        self,
        company: CompanyRef,
        *,
        query: JobQueryType = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobInsights, dict]:
        slug = ops.company_slug_of(company)
        req = ops.company_insights_request(slug, query)
        data = await self._c._request(req)
        return ops.parse_insights(data, self._c, return_type)
