"""HTTP client for the Hirebase API."""

from __future__ import annotations

from typing import Any, Optional, List

import httpx

from .config import Config, get_config


class APIError(Exception):
    """Raised when an API request fails."""
    
    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"API Error ({status_code}): {message}")


class HirebaseClient:
    """HTTP client for the Hirebase API."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the client with configuration."""
        self.config = config or get_config()
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.api_url,
                headers={
                    "X-API-Key": self.config.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise errors if needed."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", error_data.get("message", "Unknown error"))
            except Exception:
                message = response.text or "Unknown error"
            raise APIError(response.status_code, message)
        
        if response.status_code == 204:
            return None
        
        try:
            return response.json()
        except Exception:
            return response.text
    
    def get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """Make a GET request to the API."""
        response = self.client.get(endpoint, params=params)
        return self._handle_response(response)
    
    def post(self, endpoint: str, data: Optional[dict] = None) -> Any:
        """Make a POST request to the API."""
        response = self.client.post(endpoint, json=data)
        return self._handle_response(response)
    
    def put(self, endpoint: str, data: Optional[dict] = None) -> Any:
        """Make a PUT request to the API."""
        response = self.client.put(endpoint, json=data)
        return self._handle_response(response)
    
    def patch(self, endpoint: str, data: Optional[dict] = None) -> Any:
        """Make a PATCH request to the API."""
        response = self.client.patch(endpoint, json=data)
        return self._handle_response(response)
    
    def delete(self, endpoint: str) -> Any:
        """Make a DELETE request to the API."""
        response = self.client.delete(endpoint)
        return self._handle_response(response)
    
    # ==================== Jobs API ====================
    
    def search_jobs(
        self,
        job_titles: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        company_keywords: Optional[list[str]] = None,
        geo_locations: Optional[list[dict]] = None,
        days_ago: Optional[int] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> dict:
        """Search for jobs."""
        data = {
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": page,
            "limit": limit,
        }
        if job_titles:
            data["job_titles"] = job_titles
        if keywords:
            data["keywords"] = keywords
        if company_keywords:
            data["company_keywords"] = company_keywords
        if geo_locations:
            data["geo_locations"] = geo_locations
        if days_ago is not None:
            data["days_ago"] = days_ago
        
        return self.post("/v2/jobs/search", data)
    
    def get_job(self, job_id: str) -> dict:
        """Get a job by ID."""
        return self.get(f"/v2/jobs/{job_id}")
    
    def get_job_by_slug(self, company_slug: str, job_slug: str) -> dict:
        """Get a job by company slug and job slug."""
        return self.get(f"/v2/hirebase/companies/{company_slug}/jobs/{job_slug}")
    
    # ==================== Blog API ====================
    
    def list_articles(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> list[dict]:
        """List blog articles with optional filters (includes drafts)."""
        params = {
            "skip": skip,
            "limit": limit,
        }
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        return self.get("/v2/blog/admin/articles", params=params)
    
    def get_article(self, slug: str) -> dict:
        """Get a blog article by slug."""
        return self.get(f"/v2/blog/articles/{slug}")
    
    def create_article(self, article: dict) -> dict:
        """Create a new blog article."""
        return self.post("/v2/blog/admin/articles", article)
    
    def update_article(self, article_id: str, article: dict) -> dict:
        """Update a blog article."""
        return self.put(f"/v2/blog/admin/articles/{article_id}", article)
    
    def delete_article(self, article_id: str) -> dict:
        """Delete a blog article."""
        return self.delete(f"/v2/blog/admin/articles/{article_id}")
    
    # ==================== Companies API ====================
    
    def get_company(self, company_slug: str) -> dict:
        """Get a company by slug with its jobs."""
        return self.get(f"/v2/company/{company_slug}")
    
    def search_companies(
        self,
        company_name: Optional[str] = None,
        query: Optional[str] = None,
        geo_locations: Optional[dict] = None,
        industries: Optional[list[str]] = None,
        subindustries: Optional[list[str]] = None,
        company_types: Optional[list[str]] = None,
        job_board: Optional[str] = None,
        linkedin_link: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict:
        """Search for companies."""
        data = {
            "page": page,
            "limit": limit,
        }
        if company_name:
            data["company_name"] = company_name
        if query:
            data["query"] = query
        if geo_locations:
            data["geo_locations"] = geo_locations
        if industries:
            data["industries"] = industries
        if subindustries:
            data["subindustries"] = subindustries
        if company_types:
            data["company_types"] = company_types
        if job_board:
            data["job_board"] = job_board
        if linkedin_link:
            data["linkedin_link"] = linkedin_link
        
        return self.post("/v2/hirebase/companies/search", data)
    
    # ==================== Scraper Admin API ====================
    
    def query_scraper_events(
        self,
        skip: int = 0,
        limit: int = 10,
        spider_name: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        close_reason: Optional[str] = None,
        items_scraped: int = 0,
        pid: Optional[int] = None,
        server: Optional[str] = None,
    ) -> dict:
        """Query scraper events."""
        params = {
            "skip": skip,
            "limit": limit,
            "items_scraped": items_scraped,
        }
        if spider_name:
            params["spider_name"] = spider_name
        if status:
            params["status"] = status
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if close_reason:
            params["close_reason"] = close_reason
        if pid is not None:
            params["pid"] = pid
        if server:
            params["server"] = server
        
        return self.get("/v2/hirebase/scraper/admin/query", params=params)
    
    # ==================== Health API ====================
    
    def health(self) -> dict:
        """Check API health."""
        return self.get("/v2/health")


# Singleton instance
_client: Optional[HirebaseClient] = None


def get_client() -> HirebaseClient:
    """Get or create the singleton client instance."""
    global _client
    if _client is None:
        _client = HirebaseClient()
    return _client
