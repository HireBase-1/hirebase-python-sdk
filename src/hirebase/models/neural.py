"""Neural (hybrid vector + lexical) job search models."""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .jobs import Job, JobQuery, coerce_query

EMBEDDING_DIM = 768


class NeuralVectorQuery(BaseModel):
    """Semantic side of ``POST /v2/jobs/neural-search``.

    Provide any combination of ``query``, ``vectors``, ``job_ids``, and
    ``artifact_id`` (stored resume id). Pass ``resume_id`` as an alias for
    ``artifact_id``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    query: Optional[str] = Field(
        default=None,
        description="Free-text query encoded into a 768-d embedding.",
    )
    vectors: Optional[List[List[float]]] = Field(
        default=None,
        description="Explicit 768-dimensional embedding vectors.",
    )
    job_ids: Optional[List[str]] = Field(
        default=None,
        description="Find jobs similar to these job ids.",
    )
    artifact_id: Optional[str] = Field(
        default=None,
        description="Resume artifact id (from upload/embed flows).",
        validation_alias=AliasChoices("artifact_id", "resume_id"),
    )
    score_threshold: float = Field(
        default=0.0,
        description="Minimum vector similarity score (0.0–1.0).",
    )

    def to_payload(self) -> dict:
        payload: dict = {"score_threshold": self.score_threshold}
        if self.query is not None:
            payload["query"] = self.query
        if self.vectors is not None:
            for v in self.vectors:
                if len(v) != EMBEDDING_DIM:
                    raise ValueError(
                        f"Each vector must be {EMBEDDING_DIM} elements, got {len(v)}"
                    )
            payload["vectors"] = self.vectors
        if self.job_ids:
            payload["job_ids"] = self.job_ids
        if self.artifact_id:
            payload["artifact_id"] = self.artifact_id
        return payload


class NeuralSearchQuery(BaseModel):
    """Full neural-search request body."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    vector: Optional[NeuralVectorQuery] = None
    lexical: Optional[JobQuery] = None

    def to_payload(self) -> dict:
        return {
            "vector": (self.vector or NeuralVectorQuery()).to_payload(),
            "lexical": (self.lexical or JobQuery()).to_payload(),
        }


def coerce_neural_vector(
    vector: Optional[Union[NeuralVectorQuery, dict]] = None,
    *,
    query: Optional[str] = None,
    vectors: Optional[List[List[float]]] = None,
    job_ids: Optional[List[str]] = None,
    artifact_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    score_threshold: Optional[float] = None,
    **extra: Any,
) -> NeuralVectorQuery:
    """Build a ``NeuralVectorQuery`` from a model, dict, and/or keyword shortcuts."""
    if vector is None:
        base: dict = {}
    elif isinstance(vector, NeuralVectorQuery):
        base = vector.model_dump(exclude_none=True)
    elif isinstance(vector, dict):
        base = dict(vector)
    else:
        raise TypeError(
            f"vector must be a NeuralVectorQuery or dict, got {type(vector).__name__}"
        )

    if query is not None:
        base["query"] = query
    if vectors is not None:
        base["vectors"] = vectors
    if job_ids is not None:
        base["job_ids"] = job_ids
    aid = artifact_id or resume_id
    if aid is not None:
        base["artifact_id"] = aid
    if score_threshold is not None:
        base["score_threshold"] = score_threshold
    base.update({k: v for k, v in extra.items() if v is not None})
    return NeuralVectorQuery(**base)


def coerce_neural_search(
    query: Optional[Union[NeuralSearchQuery, dict]] = None,
    *,
    vector: Optional[Union[NeuralVectorQuery, dict]] = None,
    lexical: Optional[Union[JobQuery, dict]] = None,
    **vector_kwargs: Any,
) -> NeuralSearchQuery:
    if query is None:
        return NeuralSearchQuery(
            vector=coerce_neural_vector(vector, **vector_kwargs) if vector_kwargs or vector else None,
            lexical=coerce_query(lexical) if lexical is not None else None,
        )
    if isinstance(query, NeuralSearchQuery):
        return query
    if isinstance(query, dict):
        v = query.get("vector")
        lex = query.get("lexical")
        return NeuralSearchQuery(
            vector=coerce_neural_vector(v, **vector_kwargs) if v or vector_kwargs else None,
            lexical=coerce_query(lex) if lex is not None else None,
        )
    raise TypeError(
        f"query must be a NeuralSearchQuery or dict, got {type(query).__name__}"
    )


def extract_job_id(job: Union[Job, dict, str]) -> str:
    if isinstance(job, str):
        return job
    if isinstance(job, Job):
        if not job.id:
            raise ValueError("Job has no id; fetch it by id or slug first.")
        return str(job.id)
    if isinstance(job, dict):
        jid = job.get("id") or job.get("_id")
        if jid:
            return str(jid)
    raise ValueError("Could not extract a job id from the provided job reference.")


def merge_job_ids(
    vector: NeuralVectorQuery,
    *,
    job: Optional[Union[Job, dict, str]] = None,
    jobs: Optional[List[Union[Job, dict, str]]] = None,
    job_ids: Optional[List[str]] = None,
) -> NeuralVectorQuery:
    """Append ids resolved from ``job``, ``jobs``, and ``job_ids``."""
    collected = list(vector.job_ids or [])
    if job_ids:
        collected.extend(str(j) for j in job_ids)
    if job is not None:
        collected.append(extract_job_id(job))
    for item in jobs or []:
        collected.append(extract_job_id(item))
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for jid in collected:
        if jid not in seen:
            seen.add(jid)
            unique.append(jid)
    return vector.model_copy(update={"job_ids": unique or None})
