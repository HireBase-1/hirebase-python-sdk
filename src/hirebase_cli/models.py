"""Pydantic models for Hirebase API responses."""

from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field


# ==================== Location Models ====================

class Coordinates(BaseModel):
    """Geographic coordinates."""
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class Location(BaseModel):
    """Location information."""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    bbox: Optional[List[float]] = None
    address: Optional[str] = None
    
    def format_short(self) -> str:
        """Format location as short string."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country and self.country != "United States":
            parts.append(self.country)
        return ", ".join(parts) if parts else "Unknown"


# ==================== Salary Models ====================

class SalaryRange(BaseModel):
    """Salary range information."""
    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    
    def format_short(self) -> str:
        """Format salary range as short string."""
        if self.min is None and self.max is None:
            return "Not specified"
        
        def fmt(val: int) -> str:
            if val >= 1000:
                return f"${val // 1000}k"
            return f"${val}"
        
        if self.min and self.max:
            return f"{fmt(self.min)} - {fmt(self.max)}/{self.period[:1] if self.period else 'N/A'}"
        elif self.min:
            return f"{fmt(self.min)}+/{self.period[:1] if self.period else 'N/A'}"
        else:
            return f"Up to {fmt(self.max)}/{self.period[:1] if self.period else 'N/A'}"


class YoeRange(BaseModel):
    """Years of experience range."""
    min: int = 0
    max: int = 0
    
    def format_short(self) -> str:
        """Format YoE range as short string."""
        if self.min == 0 and self.max == 0:
            return "Entry level"
        if self.min == self.max:
            return f"{self.min} years"
        return f"{self.min}-{self.max} years"


# ==================== Company Models ====================

class CompanyData(BaseModel):
    """Embedded company data."""
    description_summary: Optional[str] = None
    linkedin_link: Optional[str] = None
    size_range: Optional[dict] = None
    industries: Optional[List[str]] = None
    subindustries: Optional[List[str]] = None


class CompanySearchItem(BaseModel):
    """Company search result item."""
    company_name: str
    company_slug: str
    description_summary: Optional[str] = None
    linkedin_link: Optional[str] = None
    job_board: Optional[str] = None
    size_range: Optional[dict] = None
    industries: Optional[List[str]] = None
    subindustries: Optional[List[str]] = None
    company_logo: Optional[str] = None
    services: Optional[List[str]] = None
    score: Optional[float] = None


# ==================== Job Models ====================

class Job(BaseModel):
    """Job listing model."""
    id: Optional[str] = Field(None, alias="_id")
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    description: Optional[str] = None
    application_link: Optional[str] = None
    location_raw: Optional[str] = None
    job_type: Optional[Union[str, List[str]]] = None
    location_type: Optional[Union[str, List[str]]] = None
    date_posted: Optional[str] = None
    company_link: Optional[str] = None
    company_logo: Optional[str] = None
    job_board: Optional[str] = None
    job_board_link: Optional[str] = None
    company_slug: Optional[str] = None
    language: Optional[str] = None
    requirements_summary: Optional[str] = None
    job_categories: Optional[List[str]] = None
    locations: Optional[List[Location]] = None
    education_level: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    yoe_range: Optional[YoeRange] = None
    visa_sponsored: Optional[bool] = None
    technologies: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    team: Optional[str] = None
    recruiter_agency: Optional[bool] = None
    company_data: Optional[CompanyData] = None
    job_slug: Optional[str] = None
    expired: Optional[bool] = None
    benefits: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    description_raw: Optional[str] = None
    score: Optional[float] = None
    
    class Config:
        populate_by_name = True


# ==================== Blog Models ====================

class BlogArticle(BaseModel):
    """Blog article model."""
    id: Optional[str] = Field(None, alias="_id")
    title: str
    slug: str
    author: str
    content: str
    image_url: str
    time_to_read: int
    category: str
    tags: List[str]
    table_of_contents: List[dict] = []
    meta_title: str
    meta_description: str
    og_image: str
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    view_count: int = 0
    featured: bool = False
    
    class Config:
        populate_by_name = True


# ==================== Scraper Models ====================

class ScraperEventItem(BaseModel):
    """Scraper event item."""
    id: Optional[str] = Field(None, alias="_id")
    spider_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    close_reason: Optional[str] = None
    items_scraped: int = 0
    pid: Optional[int] = None
    server: Optional[str] = None
    
    class Config:
        populate_by_name = True


# ==================== Response Models ====================

class JobSearchResponse(BaseModel):
    """Response from job search endpoint."""
    jobs: List[Job]
    total_count: int
    company_count: int
    page: int
    limit: int
    total_pages: int


class CompanySearchResponse(BaseModel):
    """Response from company search endpoint."""
    companies: List[CompanySearchItem]
    total_count: int
    page: int
    limit: int
    total_pages: int


class ScraperEventsResponse(BaseModel):
    """Response from scraper events query endpoint."""
    events: List[ScraperEventItem]


class HealthResponse(BaseModel):
    """Response from health endpoint."""
    status: str
    version: str
