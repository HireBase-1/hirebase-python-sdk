"""The ``jobs`` resource: search, get, export, insights and streaming.

Every metered method accepts ``return_meta=True`` to also receive a
:class:`hirebase.ResponseMeta` for that call (status code, headers and the
parsed ``Hirebase-Usage-*`` quota snapshot)::

    jobs, meta = client.jobs.search(query, limit=50, return_meta=True)
    print(meta.usage.included_remaining)
"""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
    overload,
)

from .. import _ops as ops
from ..models.jobs import Job, JobQuery, JobSearchResult, SalaryBenchmarkRequest
from ..models.neural import NeuralSearchQuery, NeuralVectorQuery, coerce_neural_search
from ..models.insights import JobInsights
from ..models.tasks import Task
from ..models.usage import ResponseMeta
from ..streaming import iter_jsonl_lines, stream_jobs_file

QueryType = Optional[Union[JobQuery, dict]]
SalaryBenchmarkType = Optional[Union[SalaryBenchmarkRequest, dict]]
NeuralQueryType = Optional[Union[NeuralSearchQuery, dict]]
VectorType = Optional[Union[NeuralVectorQuery, dict]]

SearchReturn = Union[JobSearchResult, dict]
JobReturn = Union[Job, dict]
InsightsReturn = Union[JobInsights, dict]


class JobsResource:
    """Synchronous jobs API."""

    def __init__(self, client) -> None:
        self._c = client

    def _call(
        self, req: ops.Request, parse: Callable[[Any], Any], return_meta: bool
    ) -> Any:
        """Send ``req`` and parse the body; attach a ``ResponseMeta`` on request."""
        if return_meta:
            data, meta = self._c._request_meta(req)
            return parse(data), meta
        return parse(self._c._request(req))

    # ── search ──────────────────────────────────────────────────────────

    @overload
    def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> SearchReturn: ...

    @overload
    def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[SearchReturn, ResponseMeta]: ...

    def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        """Search jobs. Returns a paginated, iterable result.

        With ``return_meta=True`` returns ``(result, meta)``; ``meta.usage``
        is the quota snapshot after this call.
        """
        req = ops.search_jobs_request(query, page=page, limit=limit)
        return self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    # ── get ─────────────────────────────────────────────────────────────

    @overload
    def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> JobReturn: ...

    @overload
    def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[JobReturn, ResponseMeta]: ...

    def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[JobReturn, Tuple[JobReturn, ResponseMeta]]:
        """Fetch a single job by id."""
        req = ops.get_job_request(job_id)
        return self._call(
            req, lambda d: ops.parse_job(d, self._c, return_type), return_meta
        )

    # ── exports / tasks ─────────────────────────────────────────────────

    def export(
        self,
        query: QueryType = None,
        *,
        format: str = "json",
        return_meta: bool = False,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        """Kick off an async export. Returns the created Task.

        Poll it with ``client.tasks.poll(task)``.
        """
        req = ops.export_jobs_request(query, format=format)
        return self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    def estimate(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_meta: bool = False,
    ) -> Union[int, Tuple[int, ResponseMeta]]:
        """Return how many jobs a search would bill (``min(limit, matches)``).

        Free to call, even at a block-mode cap.
        """
        req = ops.estimate_jobs_request(query, page=page, limit=limit)
        return self._call(req, lambda d: int(d["cost"]), return_meta)

    def expired(
        self,
        since: str,
        *,
        page: int = 1,
        limit: int = 100,
        return_meta: bool = False,
    ) -> Union[dict, Tuple[dict, ResponseMeta]]:
        """List expired jobs since ``since`` (ISO date or datetime)."""
        req = ops.expired_jobs_request(since, page=page, limit=limit)
        return self._call(req, lambda d: d, return_meta)

    def export_expired(
        self,
        since: str,
        *,
        limit: Optional[int] = None,
        notify: bool = False,
        return_meta: bool = False,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        """Kick off an async JSONL export of expired jobs since ``since``."""
        req = ops.export_expired_jobs_request(since, limit=limit, notify=notify)
        return self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    def salary_benchmark(
        self,
        payload: SalaryBenchmarkType = None,
        *,
        return_meta: bool = False,
        **fields,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        """Queue a posted-salary benchmark. Poll with ``client.tasks.poll``."""
        req = ops.salary_benchmark_request(payload, **fields)
        return self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    # ── semantic search ─────────────────────────────────────────────────

    def vsearch(
        self,
        query: QueryType = None,
        *,
        search_type: str = "summary",
        text: Optional[str] = None,
        job_id: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        """Vector search. ``search_type`` is ``summary``, ``job``, or ``resume``."""
        req = ops.vsearch_jobs_request(
            query,
            search_type=search_type,
            text=text,
            job_id=job_id,
            page=page,
            limit=limit,
        )
        return self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    def insights(
        self,
        query: QueryType = None,
        *,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[InsightsReturn, Tuple[InsightsReturn, ResponseMeta]]:
        """Live market insights for the cohort matching ``query``."""
        req = ops.insights_request(query)
        return self._call(
            req, lambda d: ops.parse_insights(d, self._c, return_type), return_meta
        )

    def neural_search(
        self,
        query: NeuralQueryType = None,
        *,
        vector: VectorType = None,
        lexical: QueryType = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        # Vector shortcuts (merged into ``vector``)
        text: Optional[str] = None,
        query_text: Optional[str] = None,
        vectors: Optional[list] = None,
        job_ids: Optional[list] = None,
        job: Optional[Union[Job, dict, str]] = None,
        jobs: Optional[list] = None,
        resume_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        company_slug: Optional[str] = None,
        job_slug: Optional[str] = None,
        score_threshold: Optional[float] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        """Hybrid lexical + semantic job search.

        Pass a ``NeuralSearchQuery``, a dict with ``vector`` / ``lexical`` keys,
        or use the keyword shortcuts. At least one vector or lexical signal is
        required on the API side.

        Vector inputs:
        - ``text`` / ``query_text`` / ``vector.query`` — natural-language query
        - ``vectors`` — explicit 768-d embeddings (from :meth:`resumes.embed`)
        - ``job_ids``, ``job``, ``jobs`` — similar-to-job search
        - ``resume_id`` / ``artifact_id`` — match jobs to an uploaded resume
        - ``company_slug`` + ``job_slug`` — resolved to a job id automatically

        See https://www.hirebase.org/docs/api-reference/jobs/neural-search-post
        """
        search = coerce_neural_search(query, vector=vector, lexical=lexical)
        vec = ops.prepare_neural_vector(
            self._c,
            search.vector,
            query=text or query_text,
            vectors=vectors,
            job_ids=job_ids,
            job=job,
            jobs=jobs,
            artifact_id=artifact_id,
            resume_id=resume_id,
            company_slug=company_slug,
            job_slug=job_slug,
            score_threshold=score_threshold,
        )
        search = NeuralSearchQuery(vector=vec, lexical=search.lexical)
        req = ops.neural_search_request(search, page=page, limit=limit)
        return self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    # ── streaming (local / download, un-metered) ────────────────────────

    def stream_file(
        self,
        path: str,
        *,
        return_type: Optional[Type] = None,
        format: Optional[str] = None,
    ) -> Iterator[Union[Job, dict]]:
        """Stream jobs from a local export file (JSON Lines, JSON array, or CSV)."""
        return stream_jobs_file(path, return_type=return_type, fmt=format)

    def stream_url(
        self, url: str, *, return_type: Optional[Type] = None
    ) -> Iterator[Union[Job, dict]]:
        """Stream jobs directly from an export URL without saving to disk.

        Only JSON Lines exports can be streamed this way.
        """
        return iter_jsonl_lines(self._c._stream_lines(url), return_type=return_type)


class AsyncJobsResource:
    """Asynchronous jobs API."""

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
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> SearchReturn: ...

    @overload
    async def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[SearchReturn, ResponseMeta]: ...

    async def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        req = ops.search_jobs_request(query, page=page, limit=limit)
        return await self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    @overload
    async def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: Literal[False] = False,
    ) -> JobReturn: ...

    @overload
    async def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: Literal[True],
    ) -> Tuple[JobReturn, ResponseMeta]: ...

    async def get(
        self,
        job_id: str,
        *,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[JobReturn, Tuple[JobReturn, ResponseMeta]]:
        req = ops.get_job_request(job_id)
        return await self._call(
            req, lambda d: ops.parse_job(d, self._c, return_type), return_meta
        )

    async def export(
        self,
        query: QueryType = None,
        *,
        format: str = "json",
        return_meta: bool = False,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        req = ops.export_jobs_request(query, format=format)
        return await self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    async def estimate(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_meta: bool = False,
    ) -> Union[int, Tuple[int, ResponseMeta]]:
        req = ops.estimate_jobs_request(query, page=page, limit=limit)
        return await self._call(req, lambda d: int(d["cost"]), return_meta)

    async def expired(
        self,
        since: str,
        *,
        page: int = 1,
        limit: int = 100,
        return_meta: bool = False,
    ) -> Union[dict, Tuple[dict, ResponseMeta]]:
        req = ops.expired_jobs_request(since, page=page, limit=limit)
        return await self._call(req, lambda d: d, return_meta)

    async def export_expired(
        self,
        since: str,
        *,
        limit: Optional[int] = None,
        notify: bool = False,
        return_meta: bool = False,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        req = ops.export_expired_jobs_request(since, limit=limit, notify=notify)
        return await self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    async def salary_benchmark(
        self,
        payload: SalaryBenchmarkType = None,
        *,
        return_meta: bool = False,
        **fields,
    ) -> Union[Task, Tuple[Task, ResponseMeta]]:
        """Queue a posted-salary benchmark. Poll with ``client.tasks.poll``."""
        req = ops.salary_benchmark_request(payload, **fields)
        return await self._call(
            req, lambda d: ops.parse_task(d, self._c, None), return_meta
        )

    async def vsearch(
        self,
        query: QueryType = None,
        *,
        search_type: str = "summary",
        text: Optional[str] = None,
        job_id: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        req = ops.vsearch_jobs_request(
            query,
            search_type=search_type,
            text=text,
            job_id=job_id,
            page=page,
            limit=limit,
        )
        return await self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    async def insights(
        self,
        query: QueryType = None,
        *,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[InsightsReturn, Tuple[InsightsReturn, ResponseMeta]]:
        req = ops.insights_request(query)
        return await self._call(
            req, lambda d: ops.parse_insights(d, self._c, return_type), return_meta
        )

    async def neural_search(
        self,
        query: NeuralQueryType = None,
        *,
        vector: VectorType = None,
        lexical: QueryType = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        text: Optional[str] = None,
        query_text: Optional[str] = None,
        vectors: Optional[list] = None,
        job_ids: Optional[list] = None,
        job: Optional[Union[Job, dict, str]] = None,
        jobs: Optional[list] = None,
        resume_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        company_slug: Optional[str] = None,
        job_slug: Optional[str] = None,
        score_threshold: Optional[float] = None,
        return_type: Optional[Type] = None,
        return_meta: bool = False,
    ) -> Union[SearchReturn, Tuple[SearchReturn, ResponseMeta]]:
        search = coerce_neural_search(query, vector=vector, lexical=lexical)
        vec = ops.prepare_neural_vector(
            self._c,
            search.vector,
            query=text or query_text,
            vectors=vectors,
            job_ids=job_ids,
            job=job,
            jobs=jobs,
            artifact_id=artifact_id,
            resume_id=resume_id,
            company_slug=company_slug,
            job_slug=job_slug,
            score_threshold=score_threshold,
        )
        search = NeuralSearchQuery(vector=vec, lexical=search.lexical)
        req = ops.neural_search_request(search, page=page, limit=limit)
        return await self._call(
            req, lambda d: ops.parse_job_search(d, self._c, return_type), return_meta
        )

    def stream_file(
        self,
        path: str,
        *,
        return_type: Optional[Type] = None,
        format: Optional[str] = None,
    ) -> Iterator[Union[Job, dict]]:
        """Stream jobs from a local export file (synchronous local IO)."""
        return stream_jobs_file(path, return_type=return_type, fmt=format)

    async def stream_url(
        self, url: str, *, return_type: Optional[Type] = None
    ) -> AsyncIterator[Union[Job, dict]]:
        """Async-stream jobs directly from a JSON Lines export URL."""
        async for record in self._c._astream_records(url, return_type):
            yield record
