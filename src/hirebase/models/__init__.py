"""Typed models for the Hirebase public API.

These mirror the shapes returned by https://api.hirebase.org. The SDK owns
these definitions on purpose: it is a public package and must not depend on
any private Hirebase repositories.

All response models allow unknown fields (``extra="allow"``) so the SDK keeps
working when the API adds new fields before the SDK is updated.
"""

from .base import BoundModel
from .common import CompanySizeRange, Location, SalaryRange, YoeRange
from .jobs import Job, JobQuery, JobSearchResult
from .companies import (
    Company,
    CompanyFunding,
    CompanyHeadquarters,
    CompanyQuery,
    CompanySearchResult,
    CompanyStock,
)
from .tasks import Task, TaskState
from .insights import JobInsights
from .neural import NeuralSearchQuery, NeuralVectorQuery
from .resumes import EmbeddingResult, ResumeEmbedResponse, ResumeRecord

__all__ = [
    "BoundModel",
    "Location",
    "SalaryRange",
    "YoeRange",
    "CompanySizeRange",
    "Job",
    "JobQuery",
    "JobSearchResult",
    "Company",
    "CompanyQuery",
    "CompanySearchResult",
    "CompanyHeadquarters",
    "CompanyStock",
    "CompanyFunding",
    "Task",
    "TaskState",
    "JobInsights",
    "NeuralVectorQuery",
    "NeuralSearchQuery",
    "ResumeRecord",
    "ResumeEmbedResponse",
    "EmbeddingResult",
]
