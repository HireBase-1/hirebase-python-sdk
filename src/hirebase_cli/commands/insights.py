"""Insights commands – job market trends, roles, and locations."""

from __future__ import annotations

from typing import Optional

import typer

from ..client import get_client, APIError
from ..formatters import format_error, format_json

app = typer.Typer(
    name="insights",
    help="Job market insights: trending roles, locations, salaries, and momentum",
)

def _run(output_json: bool, result: dict) -> None:
    """Output result as JSON (insights are structured; use --json for raw)."""
    format_json(result)


# --- Summary & market ---


@app.command("summary")
def summary(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """High-level insights summary (stats, market momentum, average salary US)."""
    try:
        client = get_client()
        result = client.insights_summary()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("market-momentum")
def market_momentum(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Market momentum metrics (velocity, positive/negative/neutral counts)."""
    try:
        client = get_client()
        result = client.insights_market_momentum()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("average-salary-us")
def average_salary_us(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Average salary (US) stats: average, min, max, sample size."""
    try:
        client = get_client()
        result = client.insights_average_salary_us()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


# --- Global roles (paginated: limit 1–20) ---


@app.command("trending-roles")
def trending_roles(
    limit: int = typer.Option(10, "--limit", "-n", help="Max items (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Trending roles by velocity/acceleration."""
    try:
        client = get_client()
        result = client.insights_trending_roles(limit=limit, skip=skip)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("declining-roles")
def declining_roles(
    limit: int = typer.Option(5, "--limit", "-n", help="Max items (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Roles with declining momentum."""
    try:
        client = get_client()
        result = client.insights_declining_roles(limit=limit, skip=skip)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("top-roles")
def top_roles(
    limit: int = typer.Option(5, "--limit", "-n", help="Max items (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Top roles globally by job count."""
    try:
        client = get_client()
        result = client.insights_top_roles(limit=limit, skip=skip)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("fastest-growing-roles")
def fastest_growing_roles(
    limit: int = typer.Option(5, "--limit", "-n", help="Max items (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Fastest-growing roles globally."""
    try:
        client = get_client()
        result = client.insights_fastest_growing_roles(limit=limit, skip=skip)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("highest-paying-roles")
def highest_paying_roles(
    limit: int = typer.Option(5, "--limit", "-n", help="Max items (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Highest-paying roles globally."""
    try:
        client = get_client()
        result = client.insights_highest_paying_roles(limit=limit, skip=skip)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


# --- Locations ---


@app.command("hottest-locations")
def hottest_locations(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Hottest locations by job activity."""
    try:
        client = get_client()
        result = client.insights_hottest_locations()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("locations-by-momentum")
def locations_by_momentum(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Locations ranked by momentum."""
    try:
        client = get_client()
        result = client.insights_locations_by_momentum()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


# --- Roles by location (optional location_key) ---


@app.command("top-roles-by-location")
def top_roles_by_location(
    location_key: Optional[str] = typer.Option(
        None, "--location", "-l",
        help="Location key (e.g. City|Region|Country). Omit for all locations.",
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Max items per location (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Top roles for a location, or all locations if --location omitted."""
    try:
        client = get_client()
        result = client.insights_top_roles_by_location(
            location_key=location_key, limit=limit, skip=skip
        )
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("hottest-roles-by-location")
def hottest_roles_by_location(
    location_key: Optional[str] = typer.Option(
        None, "--location", "-l",
        help="Location key. Omit for all locations.",
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Max items per location (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Hottest roles for a location, or all locations if omitted."""
    try:
        client = get_client()
        result = client.insights_hottest_roles_by_location(
            location_key=location_key, limit=limit, skip=skip
        )
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("salary-leaders-by-location")
def salary_leaders_by_location(
    location_key: Optional[str] = typer.Option(
        None, "--location", "-l",
        help="Location key. Omit for all locations.",
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Max items per location (1–20)"),
    skip: int = typer.Option(0, "--skip", help="Skip N items"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Salary leaders for a location, or all locations if omitted."""
    try:
        client = get_client()
        result = client.insights_salary_leaders_by_location(
            location_key=location_key, limit=limit, skip=skip
        )
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("role-diversity-by-location")
def role_diversity_by_location(
    location_key: Optional[str] = typer.Option(
        None, "--location", "-l",
        help="Location key. Omit for all locations.",
    ),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Role diversity stats for a location, or all locations if omitted."""
    try:
        client = get_client()
        result = client.insights_role_diversity_by_location(location_key=location_key)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


# --- Single role & catalogs ---


@app.command("role")
def role_detail(
    slug: str = typer.Argument(..., help="Role slug (e.g. job-title--city-region-country)"),
    history: int = typer.Option(10, "--history", "-H", help="History points (1–100)"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Detail and history for a single role by slug."""
    try:
        client = get_client()
        result = client.insights_role(slug=slug, history=history)
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("data-locations")
def data_locations(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """List available location keys (catalog)."""
    try:
        client = get_client()
        result = client.insights_data_locations()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("data-roles")
def data_roles(
    output_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """List available role slugs (catalog)."""
    try:
        client = get_client()
        result = client.insights_data_roles()
        _run(output_json, result)
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)
