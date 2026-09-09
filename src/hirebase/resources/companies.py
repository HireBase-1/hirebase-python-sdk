"""The ``companies`` resource: search, get, jobs and insights.

Every metered method accepts ``return_meta=True`` to also receive a
:class:`hirebase.ResponseMeta` for that call (see ``jobs`` for the pattern).
"""

from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Tuple, Type, Union, overload

from .. import _ops as ops
from ..models.companies import Company, CompanyQuery, CompanySearchResult
from ..models.insights import JobInsights
from ..models.jobs import JobQuery, JobSearchResult
from ..models.usage import ResponseMeta

CompanyQueryType = Optional[Union[CompanyQuery, dict]]
JobQueryType = Optional[Union[JobQuery, dict]]
CompanyRef = Union[Company, dict, str]

CompanySearchReturn = Union[CompanySearchResult, dict]
CompanyReturn = Union[Company, dict]
JobsReturn = Union[JobSearchResult, dict]
InsightsReturn = Union[JobInsights, dict]


def _attach_insights(company: Any, insights: Any) -> None:
    if isinstance(company, dict):
        company["insights"] = (
            insights if isinstance(insights, dict) else insights.model_dump()
        )
    else:
        company.insights_data = insights


class CompaniesResource:
    """Synchronous companies API."""

    def __init__(self, client) -> None:
        self._c = client

    def _call(
        self, req: ops.Request, parse: Callable[[Any], Any], return_meta: bool
    ) -> Any:
        if return_meta:
            data, meta = self._c._request_meta(req)
            return parse(data), meta
        return parse(self._c._request(req))

    @overload
    def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> CompanySearchReturn: ...

    @overload
    def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[CompanySearchReturn, ResponseMeta]: ...

    def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[CompanySearchReturn, Tuple[CompanySearchReturn, ResponseMeta]]:
        req = ops.search_companies_request(query, page=page, limit=limit)
        return self._call(
            req,
            lambda d: ops.parse_company_search(d, self._c, return_type),
            return_meta,
        )

    @overload
    def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> CompanyReturn: ...

    @overload
    def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[CompanyReturn, ResponseMeta]: ...

    def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[CompanyReturn, Tuple[CompanyReturn, ResponseMeta]]:
        """Fetch a company by slug.

        Set ``return_insights=True`` to also fetch live insights (an extra
        request); they are attached at ``company.insights_data`` (typed) or
        under the ``insights`` key (dict). With ``return_meta=True`` the meta
        describes the company request, not the insights one.
        """
        req = ops.get_company_request(slug)
        result = self._call(
            req,
            lambda d: ops.parse_company_detail(
                d, self._c, return_type, return_jobs=return_jobs
            ),
            return_meta,
        )
        company = result[0] if return_meta else result
        if return_insights:
            _attach_insights(company, self.insights(slug, return_type=return_type))
        return result

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
        return_meta: bool = False,
    ) -> Union[JobsReturn, Tuple[JobsReturn, ResponseMeta]]:
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
        return self._call(
            req, lambda d: ops.parse_company_jobs(d, self._c, return_type), return_meta
        )

    def insights(
        self,
        company: CompanyRef,
        *,
        query: JobQueryType = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[InsightsReturn, Tuple[InsightsReturn, ResponseMeta]]:
        """Live insights for jobs at a company."""
        slug = ops.company_slug_of(company)
        req = ops.company_insights_request(slug, query)
        return self._call(
            req, lambda d: ops.parse_insights(d, self._c, return_type), return_meta
        )


class AsyncCompaniesResource:
    """Asynchronous companies API."""

    def __init__(self, client) -> None:
        self._c = client

    async def _call(
        self, req: ops.Request, parse: Callable[[Any], Any], return_meta: bool
    ) -> Any:
        if return_meta:
            data, meta = await self._c._request_meta(req)
            return parse(data), meta
        return parse(await self._c._request(req))

    @overload
    async def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> CompanySearchReturn: ...

    @overload
    async def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[CompanySearchReturn, ResponseMeta]: ...

    async def search(
        self,
        query: CompanyQueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[CompanySearchReturn, Tuple[CompanySearchReturn, ResponseMeta]]:
        req = ops.search_companies_request(query, page=page, limit=limit)
        return await self._call(
            req,
            lambda d: ops.parse_company_search(d, self._c, return_type),
            return_meta,
        )

    @overload
    async def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> CompanyReturn: ...

    @overload
    async def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[CompanyReturn, ResponseMeta]: ...

    async def get(
        self,
        slug: str,
        *,
        return_jobs: bool = True,
        return_insights: bool = False,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[CompanyReturn, Tuple[CompanyReturn, ResponseMeta]]:
        req = ops.get_company_request(slug)
        result = await self._call(
            req,
            lambda d: ops.parse_company_detail(
                d, self._c, return_type, return_jobs=return_jobs
            ),
            return_meta,
        )
        company = result[0] if return_meta else result
        if return_insights:
            _attach_insights(
                company, await self.insights(slug, return_type=return_type)
            )
        return result

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
        return_meta: bool = False,
    ) -> Union[JobsReturn, Tuple[JobsReturn, ResponseMeta]]:
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
        return await self._call(
            req, lambda d: ops.parse_company_jobs(d, self._c, return_type), return_meta
        )

    async def insights(
        self,
        company: CompanyRef,
        *,
        query: JobQueryType = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[InsightsReturn, Tuple[InsightsReturn, ResponseMeta]]:
        slug = ops.company_slug_of(company)
        req = ops.company_insights_request(slug, query)
        return await self._call(
            req, lambda d: ops.parse_insights(d, self._c, return_type), return_meta
        )
