"""Main entry point for the Hirebase CLI."""

import typer
from rich.console import Console

from . import __version__
from .config import ConfigError
from .commands import jobs_app, blog_app, companies_app, scraper_app, health_app, insights_app

console = Console()

# Create main app
app = typer.Typer(
    name="hirebase",
    help="Hirebase CLI - Interact with the Hirebase Jobs API",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register command groups
app.add_typer(jobs_app, name="jobs")
app.add_typer(blog_app, name="blog")
app.add_typer(companies_app, name="companies")
app.add_typer(scraper_app, name="scraper")
app.add_typer(health_app, name="health")
app.add_typer(insights_app, name="insights")


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"hirebase-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Hirebase CLI - Command line interface for the Hirebase API.
    
    [bold cyan]Environment Variables:[/bold cyan]
    
    • HIREBASE_API_KEY - Your API key for authentication (required)
    
    • HIREBASE_BASE_URL / HIREBASE_API_URL - API base URL (optional;
      defaults to https://api.hirebase.org)
    
    [bold cyan]Examples:[/bold cyan]
    
    [dim]# Search for software engineer jobs in San Francisco[/dim]
    
    $ hirebase jobs search --titles "Software Engineer" -l "San Francisco, CA, US"
    
    [dim]# Get a specific job by ID[/dim]
    
    $ hirebase jobs get 6958cfd211e2763c3491ef8b
    
    [dim]# Search for companies in the AI industry[/dim]
    
    $ hirebase companies search --industries "Tech, Software & IT Services"
    
    [dim]# List blog articles[/dim]
    
    $ hirebase blog list
    
    [dim]# Check API health[/dim]
    
    $ hirebase health
    """
    pass


# Convenience shortcuts for common commands
@app.command("search")
def search_shortcut(
    query: str = typer.Argument(..., help="Search query (job titles, keywords)"),
    location: str = typer.Option(
        None, "--location", "-l",
        help="Location filter: 'City, Region, Country'"
    ),
    days: int = typer.Option(
        None, "--days", "-d",
        help="Filter jobs posted within N days"
    ),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(10, "--limit", help="Results per page"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each job"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Quick job search shortcut. Equivalent to 'hirebase jobs search'."""
    from .commands.jobs import parse_locations, parse_list
    from .client import get_client, APIError
    from .formatters import format_job_table, format_pagination_info, format_error, format_json
    
    try:
        client = get_client()
        result = client.search_jobs(
            job_titles=parse_list(query),
            keywords=parse_list(query),
            geo_locations=parse_locations(location),
            days_ago=days,
            page=page,
            limit=limit,
        )
        
        if output_json:
            format_json(result)
        else:
            format_job_table(result.get("jobs", []), full_info=full_info)
            format_pagination_info(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except ConfigError as e:
        format_error(str(e))
        console.print("\n[dim]Set HIREBASE_API_KEY (and optionally HIREBASE_BASE_URL)[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        format_error(f"Error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
