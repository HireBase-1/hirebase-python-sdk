"""Jobs commands for the Hirebase CLI."""

from __future__ import annotations

import json
from typing import Optional, List

import typer
from rich.console import Console

from ..client import get_client, APIError
from ..formatters import (
    format_job_table, format_job_detail, format_pagination_info,
    format_error, format_json, console
)

app = typer.Typer(name="jobs", help="Search and view job listings")


def parse_locations(locations_str: Optional[str]) -> Optional[List[dict]]:
    """Parse location string into list of location dicts.
    
    Formats supported:
    - "San Francisco, California, United States"
    - "city:San Francisco,region:California,country:United States"
    - JSON: '[{"city": "San Francisco", "region": "California", "country": "United States"}]'
    """
    if not locations_str:
        return None
    
    locations_str = locations_str.strip()
    
    # Try JSON first
    if locations_str.startswith("[") or locations_str.startswith("{"):
        try:
            parsed = json.loads(locations_str)
            if isinstance(parsed, dict):
                return [parsed]
            return parsed
        except json.JSONDecodeError:
            pass
    
    # Try key:value format
    if "city:" in locations_str or "region:" in locations_str or "country:" in locations_str:
        location = {}
        parts = locations_str.split(",")
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                location[key.strip().lower()] = value.strip()
        if location:
            return [location]
    
    # Simple comma-separated format: "City, Region, Country"
    parts = [p.strip() for p in locations_str.split(",")]
    location = {}
    if len(parts) >= 1:
        location["city"] = parts[0]
    if len(parts) >= 2:
        location["region"] = parts[1]
    if len(parts) >= 3:
        location["country"] = parts[2]
    
    return [location] if location else None


def parse_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_page(value: str) -> List[int]:
    """Parse page number or range into list of page numbers.

    Supports:
    - Single page: "1" -> [1]
    - Inclusive range: "1..5" -> [1, 2, 3, 4, 5]
    """
    value = value.strip()
    if ".." in value:
        parts = value.split("..", 1)
        if len(parts) != 2:
            raise typer.BadParameter("Invalid page range. Use format: 1..5")
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
        except ValueError:
            raise typer.BadParameter("Page range must be integers (e.g. 1..5)")
        if start < 1 or end < 1:
            raise typer.BadParameter("Page numbers must be >= 1")
        if start > end:
            raise typer.BadParameter("Range start must be <= end (e.g. 1..5)")
        return list(range(start, end + 1))
    try:
        p = int(value)
        if p < 1:
            raise typer.BadParameter("Page number must be >= 1")
        return [p]
    except ValueError:
        raise typer.BadParameter("Page must be an integer or range (e.g. 1 or 1..5)")


@app.command("search")
def search(
    titles: Optional[str] = typer.Option(
        None, "--titles", "-t",
        help="Job titles to search for (comma-separated)"
    ),
    keywords: Optional[str] = typer.Option(
        None, "--keywords", "-k",
        help="Keywords to search for (comma-separated)"
    ),
    company_keywords: Optional[str] = typer.Option(
        None, "--company", "-c",
        help="Company keywords to filter by (comma-separated)"
    ),
    locations: Optional[str] = typer.Option(
        None, "--locations", "-l",
        help="Location filter: 'City, Region, Country' or JSON"
    ),
    days_ago: Optional[int] = typer.Option(
        None, "--days", "-d",
        help="Filter jobs posted within N days"
    ),
    sort_by: str = typer.Option(
        "relevance", "--sort", "-s",
        help="Sort by: relevance, date_posted"
    ),
    sort_order: str = typer.Option(
        "desc", "--order", "-o",
        help="Sort order: asc, desc"
    ),
    page: str = typer.Option(
        "1", "--page", "-p",
        help="Page number or inclusive range (e.g. 1 or 1..5)"
    ),
    limit: int = typer.Option(10, "--limit", help="Results per page (max 100)"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each job"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Search for jobs with various filters."""
    try:
        pages = parse_page(page)
        client = get_client()

        if len(pages) == 1:
            result = client.search_jobs(
                job_titles=parse_list(titles),
                keywords=parse_list(keywords),
                company_keywords=parse_list(company_keywords),
                geo_locations=parse_locations(locations),
                days_ago=days_ago,
                sort_by=sort_by,
                sort_order=sort_order,
                page=pages[0],
                limit=limit,
            )
        else:
            all_jobs: List[dict] = []
            first_result = None
            for p in pages:
                result = client.search_jobs(
                    job_titles=parse_list(titles),
                    keywords=parse_list(keywords),
                    company_keywords=parse_list(company_keywords),
                    geo_locations=parse_locations(locations),
                    days_ago=days_ago,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=p,
                    limit=limit,
                )
                if first_result is None:
                    first_result = result
                all_jobs.extend(result.get("jobs", []))
            result = {
                "jobs": all_jobs,
                "total_count": first_result.get("total_count") if first_result else 0,
                "company_count": first_result.get("company_count") if first_result else 0,
                "page_range": f"{pages[0]}..{pages[-1]}",
                "pages_fetched": len(pages),
                "limit": limit,
                "total_pages": first_result.get("total_pages") if first_result else 0,
            }

        if output_json:
            format_json(result)
        else:
            format_job_table(result.get("jobs", []), full_info=full_info)
            format_pagination_info(result)

    except typer.BadParameter:
        raise
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("get")
def get_job(
    job_id: str = typer.Argument(..., help="Job ID to retrieve"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Get a job by its ID."""
    try:
        client = get_client()
        result = client.get_job(job_id)
        
        if output_json:
            format_json(result)
        else:
            format_job_detail(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("get-by-slug")
def get_job_by_slug(
    company_slug: str = typer.Argument(..., help="Company slug"),
    job_slug: str = typer.Argument(..., help="Job slug"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Get a job by company slug and job slug."""
    try:
        client = get_client()
        result = client.get_job_by_slug(company_slug, job_slug)
        
        if output_json:
            format_json(result)
        else:
            jobs = result.get("jobs", [])
            if jobs:
                for job in jobs:
                    format_job_detail(job)
            else:
                console.print("[yellow]No job found with the specified slugs.[/yellow]")
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        format_error(f"Error: {e}")
        raise typer.Exit(1)
