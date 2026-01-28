"""Scraper commands for the Hirebase CLI."""

from typing import Optional
from datetime import datetime, timedelta

import typer
from rich.console import Console

from ..client import get_client, APIError
from ..formatters import (
    format_scraper_events_table,
    format_error, format_json, console
)

app = typer.Typer(name="scraper", help="Monitor and query scraper events")


@app.command("events")
def query_events(
    spider: Optional[str] = typer.Option(
        None, "--spider", "-s",
        help="Filter by spider name"
    ),
    status: Optional[str] = typer.Option(
        None, "--status",
        help="Filter by status: RUNNING, COMPLETED, STOPPED, FAILED, INTERRUPTED, ZOMBIE_CRASHED"
    ),
    start_time: Optional[str] = typer.Option(
        None, "--start",
        help="Start time filter (ISO format or relative like '1d', '1h', '30m'). Default: 90d"
    ),
    end_time: Optional[str] = typer.Option(
        None, "--end",
        help="End time filter (ISO format)"
    ),
    close_reason: Optional[str] = typer.Option(
        None, "--close-reason",
        help="Filter by close reason"
    ),
    min_items: int = typer.Option(
        0, "--min-items",
        help="Minimum items scraped"
    ),
    pid: Optional[int] = typer.Option(
        None, "--pid",
        help="Filter by process ID"
    ),
    server: Optional[str] = typer.Option(
        None, "--server",
        help="Filter by server name"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results to return"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each event"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Query scraper events with various filters."""
    try:
        # Parse relative time formats (default to 90 days if not specified)
        if start_time:
            start_time_parsed = parse_relative_time(start_time)
        else:
            start_time_parsed = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        end_time_parsed = parse_relative_time(end_time) if end_time else None
        
        client = get_client()
        result = client.query_scraper_events(
            skip=skip,
            limit=limit,
            spider_name=spider,
            status=status,
            start_time=start_time_parsed,
            end_time=end_time_parsed,
            close_reason=close_reason,
            items_scraped=min_items,
            pid=pid,
            server=server,
        )
        
        if output_json:
            format_json(result)
        else:
            events = result.get("events", [])
            format_scraper_events_table(events, full_info=full_info)
            console.print(f"\n[dim]Showing {len(events)} events (skip: {skip})[/dim]")
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


def parse_relative_time(time_str: str) -> str:
    """Parse time string, handling relative formats like '1d', '1h', '30m'."""
    time_str = time_str.strip()
    
    # Already ISO format
    if "T" in time_str or "-" in time_str:
        return time_str
    
    now = datetime.utcnow()
    
    # Relative formats
    if time_str.endswith("d"):
        days = int(time_str[:-1])
        return (now - timedelta(days=days)).isoformat()
    elif time_str.endswith("h"):
        hours = int(time_str[:-1])
        return (now - timedelta(hours=hours)).isoformat()
    elif time_str.endswith("m"):
        minutes = int(time_str[:-1])
        return (now - timedelta(minutes=minutes)).isoformat()
    elif time_str.endswith("w"):
        weeks = int(time_str[:-1])
        return (now - timedelta(weeks=weeks)).isoformat()
    
    return time_str
