"""Resume upload, parse, and enterprise embed models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, ConfigDict, Field

from .base import ResponseModel


class EmbeddingResult(ResponseModel):
    model_config = ConfigDict(protected_namespaces=())
    """768-d resume embedding returned by ``POST /v2/resumes/embed``."""

    embedding: List[float]
    dtype: str = "resume"
    dim: int = 768
    model_name: Optional[str] = None
    model_version: Optional[str] = None


class ResumeEmbedResponse(ResponseModel):
    """Enterprise embed: parsed resume + vector. Data is not stored server-side."""

    resume: Dict[str, Any] = Field(default_factory=dict)
    result: EmbeddingResult

    @property
    def embedding(self) -> List[float]:
        return self.result.embedding


class ResumeRecord(ResponseModel):
    """A resume stored on Hirebase (public upload flow)."""

    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("_id", "id", "artifact_id"),
    )
    user_id: Optional[str] = None
    resume_url: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
