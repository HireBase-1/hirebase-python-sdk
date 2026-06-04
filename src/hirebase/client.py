"""The public ``Client`` (sync, requests) and ``AsyncClient`` (async, httpx).

Both clients share the same resource layer and the same request/response logic
(see ``_ops.py``); only the transport differs.
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator, Iterator, Optional, Type, Union

from . import _ops as ops
from .config import Settings
from .exceptions import error_from_response
from .resources.companies import AsyncCompaniesResource, CompaniesResource
from .resources.jobs import AsyncJobsResource, JobsResource
from .resources.tasks import AsyncTasksResource, TasksResource

_DOWNLOAD_CHUNK = 1024 * 256


class Client:
    """Synchronous Hirebase API client.

    Example:
        >>> import hirebase
        >>> client = hirebase.Client(api_key="sk_live_...")
        >>> result = client.jobs.search({"job_titles": ["Software Engineer"]})
        >>> for job in result:
        ...     print(job.job_title, job.company_name)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self._settings = Settings.resolve(api_key, base_url, timeout)
        import requests  # local import keeps httpx-only users lean

        self._session = requests.Session()
        self._session.headers.update(self._settings.headers)

        self.jobs = JobsResource(self)
        self.companies = CompaniesResource(self)
        self.tasks = TasksResource(self)

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    def _url(self, path: str) -> str:
        return f"{self._settings.base_url}{path}"

    def _request(self, req: ops.Request) -> Any:
        resp = self._session.request(
            req.method,
            self._url(req.path),
            params=req.params,
            json=req.json,
            timeout=self._settings.timeout,
        )
        return _handle_response(resp.status_code, resp.content, resp)

    def stream_file(
        self, url: str, *, file_path: str, chunk_size: int = _DOWNLOAD_CHUNK
    ) -> str:
        """Download ``url`` to ``file_path``, streaming to avoid buffering.

        Returns the path written. ``url`` is typically the ``download_url`` from
        an export task result.
        """
        import requests

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with requests.get(url, stream=True, timeout=self._settings.timeout) as resp:
            _raise_for_download(resp.status_code, resp)
            with open(file_path, "wb") as handle:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        handle.write(chunk)
        return file_path

    def _stream_lines(self, url: str) -> Iterator[bytes]:
        import requests

        with requests.get(url, stream=True, timeout=self._settings.timeout) as resp:
            _raise_for_download(resp.status_code, resp)
            for line in resp.iter_lines():
                if line:
                    yield line

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class AsyncClient:
    """Asynchronous Hirebase API client.

    Example:
        >>> import hirebase, asyncio
        >>> async def main():
        ...     client = hirebase.AsyncClient(api_key="sk_live_...")
        ...     result = await client.jobs.search({"job_titles": ["Engineer"]})
        ...     await client.aclose()
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self._settings = Settings.resolve(api_key, base_url, timeout)
        import httpx

        self._http = httpx.AsyncClient(
            base_url=self._settings.base_url,
            headers=self._settings.headers,
            timeout=self._settings.timeout,
        )

        self.jobs = AsyncJobsResource(self)
        self.companies = AsyncCompaniesResource(self)
        self.tasks = AsyncTasksResource(self)

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    async def _request(self, req: ops.Request) -> Any:
        resp = await self._http.request(
            req.method, req.path, params=req.params, json=req.json
        )
        return _handle_response(resp.status_code, resp.content, resp)

    async def stream_file(
        self, url: str, *, file_path: str, chunk_size: int = _DOWNLOAD_CHUNK
    ) -> str:
        """Download ``url`` to ``file_path`` without buffering the whole body."""
        import httpx

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        async with httpx.AsyncClient(timeout=self._settings.timeout) as http:
            async with http.stream("GET", url) as resp:
                _raise_for_download(resp.status_code, resp)
                with open(file_path, "wb") as handle:
                    async for chunk in resp.aiter_bytes(chunk_size):
                        handle.write(chunk)
        return file_path

    async def _astream_records(
        self, url: str, return_type: Optional[Type]
    ) -> AsyncIterator[Union[Any, dict]]:
        from .streaming import _coerce_record  # local import: internal helper
        import httpx

        async with httpx.AsyncClient(timeout=self._settings.timeout) as http:
            async with http.stream("GET", url) as resp:
                _raise_for_download(resp.status_code, resp)
                async for line in resp.aiter_lines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    yield _coerce_record(json.loads(stripped), return_type)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()


def _decode_body(content: bytes) -> Any:
    if not content:
        return None
    try:
        return json.loads(content)
    except (ValueError, TypeError):
        try:
            return content.decode("utf-8")
        except Exception:  # pragma: no cover - defensive
            return None


def _handle_response(status_code: int, content: bytes, _resp: Any) -> Any:
    if status_code >= 400:
        raise error_from_response(status_code, _decode_body(content))
    if status_code == 204 or not content:
        return None
    return _decode_body(content)


def _raise_for_download(status_code: int, _resp: Any) -> None:
    if status_code >= 400:
        raise error_from_response(status_code, f"Failed to download file (HTTP {status_code}).")
