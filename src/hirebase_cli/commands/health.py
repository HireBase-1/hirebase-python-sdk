"""Health check command for the Hirebase CLI."""

import typer
from rich.console import Console

from ..client import get_client, APIError
from ..formatters import format_health, format_error, format_json

app = typer.Typer(name="health", help="Check API health status")


@app.callback(invoke_without_command=True)
def health(
    ctx: typer.Context,
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Check the health of the Hirebase API."""
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return
    
    try:
        client = get_client()
        result = client.health()
        
        if output_json:
            format_json(result)
        else:
            format_health(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)
