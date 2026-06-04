"""Insights model returned by jobs/companies insights endpoints.

The insights payload is large and evolving. We type the headline KPIs and the
salary block (the parts most consumers read directly) and keep everything else
as loosely-typed lists with ``extra="allow"`` so new sections never break the
SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import ResponseModel


class _Block(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class InsightsHeadline(_Block):
    total_count: int = 0
    sample_size: int = 0
    median_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    pct_disclosing_salary: float = 0.0
    pct_remote: float = 0.0
    top_company: Optional[str] = None
    top_technology: Optional[str] = None
    dominant_experience_level: Optional[str] = None
    new_this_week: int = 0


class HistogramBin(_Block):
    lower: float
    upper: float
    count: int


class SalaryStats(_Block):
    count: int = 0
    avg: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None
    histogram: List[HistogramBin] = Field(default_factory=list)
    fitted_normal: Optional[Dict[str, float]] = None


class JobInsights(ResponseModel):
    """Live, search-driven market insights for a cohort of jobs."""

    headline: InsightsHeadline = Field(default_factory=InsightsHeadline)
    salary: SalaryStats = Field(default_factory=SalaryStats)

    salary_by_level: List[Dict[str, Any]] = Field(default_factory=list)
    salary_by_location_type: List[Dict[str, Any]] = Field(default_factory=list)
    level_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    location_type_split: List[Dict[str, Any]] = Field(default_factory=list)
    job_type_split: List[Dict[str, Any]] = Field(default_factory=list)
    top_locations: List[Dict[str, Any]] = Field(default_factory=list)
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_technologies: List[Dict[str, Any]] = Field(default_factory=list)
    top_skills: List[Dict[str, Any]] = Field(default_factory=list)
    top_benefits: List[Dict[str, Any]] = Field(default_factory=list)
    education_split: List[Dict[str, Any]] = Field(default_factory=list)
    company_size_split: List[Dict[str, Any]] = Field(default_factory=list)
    industry_split: List[Dict[str, Any]] = Field(default_factory=list)
    subindustry_split: List[Dict[str, Any]] = Field(default_factory=list)

    visa_sponsorship_rate: float = 0.0
    recruiter_agency_rate: float = 0.0
    yoe_median: Optional[float] = None
    scores: List[Dict[str, Any]] = Field(default_factory=list)
    scores_by_level: List[Dict[str, Any]] = Field(default_factory=list)
    freshness: Optional[Dict[str, Any]] = None
    cached: bool = False
    generated_at: Optional[datetime] = None
