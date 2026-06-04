"""The ``jobs`` resource: search, get, export, insights and streaming."""

from __future__ import annotations

from typing import AsyncIterator, Iterator, Optional, Type, Union

from .. import _ops as ops
from ..models.jobs import Job, JobQuery, JobSearchResult
from ..models.insights import JobInsights
from ..models.tasks import Task
from ..streaming import iter_jsonl_lines, stream_jobs_file

QueryType = Optional[Union[JobQuery, dict]]


class JobsResource:
    """Synchronous jobs API."""

    def __init__(self, client) -> None:
        self._c = client

    def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobSearchResult, dict]:
        """Search jobs. Returns a paginated, iterable result."""
        req = ops.search_jobs_request(query, page=page, limit=limit)
        data = self._c._request(req)
        return ops.parse_job_search(data, self._c, return_type)

    def get(
        self, job_id: str, *, return_type: Optional[Type] = None
    ) -> Union[Job, dict]:
        """Fetch a single job by id."""
        req = ops.get_job_request(job_id)
        data = self._c._request(req)
        return ops.parse_job(data, self._c, return_type)

    def export(self, query: QueryType = None, *, format: str = "json") -> Task:
        """Kick off an async export. Returns the created Task.

        Poll it with ``client.tasks.poll(task)``.
        """
        req = ops.export_jobs_request(query, format=format)
        data = self._c._request(req)
        return ops.parse_task(data, self._c, None)  # type: ignore[return-value]

    def insights(
        self, query: QueryType = None, *, return_type: Optional[Type] = None
    ) -> Union[JobInsights, dict]:
        """Live market insights for the cohort matching ``query``."""
        req = ops.insights_request(query)
        data = self._c._request(req)
        return ops.parse_insights(data, self._c, return_type)

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

    async def search(
        self,
        query: QueryType = None,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        return_type: Optional[Type] = None,
    ) -> Union[JobSearchResult, dict]:
        req = ops.search_jobs_request(query, page=page, limit=limit)
        data = await self._c._request(req)
        return ops.parse_job_search(data, self._c, return_type)

    async def get(
        self, job_id: str, *, return_type: Optional[Type] = None
    ) -> Union[Job, dict]:
        req = ops.get_job_request(job_id)
        data = await self._c._request(req)
        return ops.parse_job(data, self._c, return_type)

    async def export(self, query: QueryType = None, *, format: str = "json") -> Task:
        req = ops.export_jobs_request(query, format=format)
        data = await self._c._request(req)
        return ops.parse_task(data, self._c, None)  # type: ignore[return-value]

    async def insights(
        self, query: QueryType = None, *, return_type: Optional[Type] = None
    ) -> Union[JobInsights, dict]:
        req = ops.insights_request(query)
        data = await self._c._request(req)
        return ops.parse_insights(data, self._c, return_type)

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
