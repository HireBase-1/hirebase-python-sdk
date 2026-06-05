"""The ``resumes`` resource: upload, parse, and enterprise embed."""

from __future__ import annotations

from typing import Optional, Type, Union

from .. import _ops as ops
from .._files import FileInput, prepare_upload_file
from ..models.resumes import ResumeEmbedResponse, ResumeRecord

FileType = FileInput


def _resume_record_id(record: Union[ResumeRecord, dict]) -> Optional[str]:
    if isinstance(record, ResumeRecord):
        return record.id
    return record.get("id") or record.get("_id")


class ResumesResource:
    """Resume upload (stored) and enterprise embed (private, returns vectors)."""

    def __init__(self, client) -> None:
        self._c = client

    def upload(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        """Upload a resume file to Hirebase (stored on our servers).

        Supported formats: PDF, Word, plain text, HTML. Max 5 MB.
        Call :meth:`parse` afterward to extract structured data, or use
        :meth:`upload_and_parse` to do both in one step.
        """
        files = prepare_upload_file(file)
        data = self._c._request(ops.resume_upload_request(files))
        return ops.parse_resume_record(data, return_type)

    def get(
        self, resume_id: str, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        """Fetch a resume by id (uploaded + optional parsed state)."""
        data = self._c._request(ops.resume_get_request(resume_id))
        return ops.parse_resume_record(data, return_type)

    def parse(
        self, resume_id: str, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        """Parse a previously uploaded resume into structured fields."""
        data = self._c._request(ops.resume_parse_request(resume_id))
        return ops.parse_resume_record(data, return_type)

    def upload_and_parse(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        """Upload a resume, parse it, then GET the canonical record."""
        record = self.upload(file, return_type=return_type)
        rid = _resume_record_id(record)
        if not rid:
            raise ValueError("Upload response did not include a resume id.")
        rid = str(rid)
        self.parse(rid, return_type=return_type)
        return self.get(rid, return_type=return_type)

    def embed(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeEmbedResponse, dict]:
        """Enterprise embed: parse the file and return a 768-d vector.

        The resume content is **not** stored on Hirebase servers. Use the
        returned ``embedding`` with :meth:`~hirebase.resources.jobs.JobsResource.neural_search`
        (``vectors=[...]``) or keep it in your own systems.

        Requires an enterprise API key with commercial embed permission.
        See https://www.hirebase.org/docs/api-reference/resumes/embed-post
        """
        files = prepare_upload_file(file)
        data = self._c._request(ops.resume_embed_request(files))
        return ops.parse_resume_embed(data, return_type)


class AsyncResumesResource:
    """Async resume upload, parse, and enterprise embed."""

    def __init__(self, client) -> None:
        self._c = client

    async def upload(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        files = prepare_upload_file(file)
        data = await self._c._request(ops.resume_upload_request(files))
        return ops.parse_resume_record(data, return_type)

    async def get(
        self, resume_id: str, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        data = await self._c._request(ops.resume_get_request(resume_id))
        return ops.parse_resume_record(data, return_type)

    async def parse(
        self, resume_id: str, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        data = await self._c._request(ops.resume_parse_request(resume_id))
        return ops.parse_resume_record(data, return_type)

    async def upload_and_parse(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeRecord, dict]:
        record = await self.upload(file, return_type=return_type)
        rid = _resume_record_id(record)
        if not rid:
            raise ValueError("Upload response did not include a resume id.")
        rid = str(rid)
        await self.parse(rid, return_type=return_type)
        return await self.get(rid, return_type=return_type)

    async def embed(
        self, file: FileType, *, return_type: Optional[Type] = None
    ) -> Union[ResumeEmbedResponse, dict]:
        files = prepare_upload_file(file)
        data = await self._c._request(ops.resume_embed_request(files))
        return ops.parse_resume_embed(data, return_type)
