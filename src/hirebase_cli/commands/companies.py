"""Companies commands for the Hirebase CLI."""

from __future__ import annotations

import json
from typing import Optional, List

import typer
from rich.console import Console

from ..client import get_client, APIError
from ..formatters import (
    format_companies_table, format_company_detail, format_pagination_info, 
    format_job_table, format_error, format_json, console
)

app = typer.Typer(name="companies", help="Search and view companies")


def parse_location(location_str: Optional[str]) -> Optional[dict]:
    """Parse location string into location dict.
    
    Formats supported:
    - "San Francisco, California, United States"
    - "city:San Francisco,region:California,country:United States"
    - JSON: '{"city": "San Francisco", "region": "California", "country": "United States"}'
    """
    if not location_str:
        return None
    
    location_str = location_str.strip()
    
    # Try JSON first
    if location_str.startswith("{"):
        try:
            return json.loads(location_str)
        except json.JSONDecodeError:
            pass
    
    # Try key:value format
    if "city:" in location_str or "region:" in location_str or "country:" in location_str:
        location = {}
        parts = location_str.split(",")
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                location[key.strip().lower()] = value.strip()
        if location:
            return location
    
    # Simple comma-separated format: "City, Region, Country"
    parts = [p.strip() for p in location_str.split(",")]
    location = {}
    if len(parts) >= 1:
        location["city"] = parts[0]
    if len(parts) >= 2:
        location["region"] = parts[1]
    if len(parts) >= 3:
        location["country"] = parts[2]
    
    return location if location else None


def parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


@app.command("search")
def search(
    names: Optional[str] = typer.Option(
        None, "--names", "-n",
        help="Company names to search for (comma-separated)"
    ),
    keywords: Optional[str] = typer.Option(
        None, "--keywords", "-k",
        help="Keywords to search for (comma-separated)"
    ),
    location: Optional[str] = typer.Option(
        None, "--location", "-l",
        help="Location filter: 'City, Region, Country' or JSON"
    ),
    industries: Optional[str] = typer.Option(
        None, "--industries", "-i",
        help="Industries to filter by (comma-separated)"
    ),
    subindustries: Optional[str] = typer.Option(
        None, "--subindustries",
        help="Subindustries to filter by (comma-separated)"
    ),
    company_types: Optional[str] = typer.Option(
        None, "--types", "-t",
        help="Company types to filter by (comma-separated)"
    ),
    job_board: Optional[str] = typer.Option(
        None, "--job-board",
        help="Filter by job board source"
    ),
    linkedin: Optional[str] = typer.Option(
        None, "--linkedin",
        help="LinkedIn URL to search for"
    ),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(10, "--limit", help="Results per page (max 100)"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each company"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Search for companies with various filters."""
    try:
        # Convert comma-separated to space-separated for API query
        company_name = " ".join(parse_list(names)) if names else None
        query = " ".join(parse_list(keywords)) if keywords else None
        
        client = get_client()
        result = client.search_companies(
            company_name=company_name,
            query=query,
            geo_locations=parse_location(location),
            industries=parse_list(industries),
            subindustries=parse_list(subindustries),
            company_types=parse_list(company_types),
            job_board=job_board,
            linkedin_link=linkedin,
            page=page,
            limit=limit,
        )
        
        if output_json:
            format_json(result)
        else:
            format_companies_table(result.get("companies", []), full_info=full_info)
            format_pagination_info(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("get")
def get_company(
    company_slug: str = typer.Argument(..., help="Company slug to retrieve"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Get detailed company information by slug.
    
    Returns company details and a sample of their jobs.
    Use this to get full information about a company found in search results.
    """
    try:
        client = get_client()
        result = client.get_company(company_slug)
        
        if output_json:
            format_json(result)
        else:
            company_data = result.get("company", {})
            jobs = result.get("jobs", [])
            format_company_detail(company_data, jobs)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("jobs")
def get_company_jobs(
    company_slug: str = typer.Argument(..., help="Company slug"),
    job_slug: Optional[str] = typer.Argument(None, help="Specific job slug (optional)"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each job"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Get jobs from a specific company by slug."""
    try:
        client = get_client()
        
        if job_slug:
            # Get specific job
            result = client.get_job_by_slug(company_slug, job_slug)
        else:
            # Get all jobs for company (using search with company filter)
            # Note: The API doesn't have a direct endpoint for this,
            # so we use the slug-based endpoint with a wildcard
            result = client.get_job_by_slug(company_slug, "*")
        
        if output_json:
            format_json(result)
        else:
            jobs = result.get("jobs", [])
            if jobs:
                format_job_table(jobs, full_info=full_info)
            else:
                console.print("[yellow]No jobs found for this company.[/yellow]")
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)
