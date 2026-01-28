"""ASCII formatters for CLI output."""

import os
from datetime import datetime
from typing import Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .models import (
    Job, BlogArticle, CompanySearchItem, ScraperEventItem,
    Location, SalaryRange
)

console = Console()


def get_web_url() -> str:
    """Get the Hirebase web URL from the API URL."""
    api_url = os.getenv("HIREBASE_API_URL", "https://api.hirebase.org")
    # Convert api.hirebase.org -> www.hirebase.org
    if "api." in api_url:
        return api_url.replace("api.", "www.")
    return api_url.replace("://", "://www.")


def generate_job_link(job: Job) -> str:
    """Generate the Hirebase web URL for a job."""
    if not job.company_slug or not job.job_slug:
        return ""
    web_url = get_web_url()
    return f"{web_url}/company/{job.company_slug}/job/{job.job_slug}"


def generate_company_link(company_slug: str) -> str:
    """Generate the Hirebase web URL for a company."""
    if not company_slug:
        return ""
    web_url = get_web_url()
    return f"{web_url}/company/{company_slug}"


def truncate(text: str, max_len: int = 50) -> str:
    """Truncate text to max length with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def wrap_text(text: str, width: int = 40, max_lines: int = 5) -> str:
    """Wrap text to fit within width and max_lines, with ellipsis if truncated."""
    if not text:
        return ""
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line) + 1 + len(word) <= width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
            if len(lines) >= max_lines:
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(current_line)
    
    # Add ellipsis if we truncated
    if len(lines) == max_lines and words:
        remaining = " ".join(words[sum(len(l.split()) for l in lines):])
        if remaining:
            last_line = lines[-1]
            if len(last_line) > width - 3:
                lines[-1] = last_line[:width - 3] + "..."
            else:
                lines[-1] = last_line + "..."
    
    return "\n".join(lines)


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "N/A"
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        return date_str
    except Exception:
        return date_str


def format_locations(locations: Optional[List[Location]]) -> str:
    """Format list of locations as string."""
    if not locations:
        return "N/A"
    formatted = []
    for loc in locations[:3]:  # Limit to 3 locations
        if isinstance(loc, dict):
            loc = Location(**loc)
        formatted.append(loc.format_short())
    result = " | ".join(formatted)
    if len(locations) > 3:
        result += f" (+{len(locations) - 3} more)"
    return result


def format_list(items: Optional[List[str]], max_items: int = 3) -> str:
    """Format list of strings."""
    if not items:
        return "N/A"
    if len(items) <= max_items:
        return ", ".join(items)
    return ", ".join(items[:max_items]) + f" (+{len(items) - max_items})"


def format_salary(salary: Optional[SalaryRange]) -> str:
    """Format salary range."""
    if not salary:
        return "N/A"
    if isinstance(salary, dict):
        salary = SalaryRange(**salary)
    return salary.format_short()


# ==================== Job Formatters ====================

def format_job_table(jobs: List[dict], full_info: bool = False) -> None:
    """Format jobs as a table."""
    if not jobs:
        console.print("[yellow]No jobs found.[/yellow]")
        return
    
    table = Table(
        title="Jobs",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=True,  # Show lines between rows for stacked content
        expand=True,  # Expand to full terminal width
    )
    
    # Core columns
    table.add_column("Job", style="green", min_width=35, max_width=50)  # Title + slugs + ID
    table.add_column("Description", style="dim", min_width=20, max_width=30)  # Requirements summary
    table.add_column("Details (Company / Location / Salary)", style="blue", min_width=25, max_width=35)  # Company / Location / Salary
    table.add_column("Link", style="cyan", max_width=256)
    
    if full_info:
        table.add_column("Type", max_width=12)
        table.add_column("Technologies", max_width=30)
    
    for job_data in jobs:
        job = Job(**job_data) if isinstance(job_data, dict) else job_data
        
        # Parse locations
        locations_str = job.location_raw or "N/A"
        if job.locations:
            locs = [Location(**l) if isinstance(l, dict) else l for l in job.locations]
            locations_str = format_locations(locs)
        
        # Build job cell: Title + slugs + ID
        job_title = job.job_title or "N/A"
        company_slug = job.company_slug or ""
        job_slug = job.job_slug or ""
        job_id = job.id or "N/A"
        
        job_cell_parts = [f"[bold]{truncate(job_title, 48)}[/bold]"]
        if company_slug and job_slug:
            job_cell_parts.append(f"[cyan]{company_slug}/{job_slug}[/cyan]")
        job_cell_parts.append(f"[dim]ID: {job_id}[/dim]")
        job_cell = "\n".join(job_cell_parts)
        
        # Description cell: requirements summary (wrap to 5 lines)
        requirements = job.requirements_summary or ""
        desc_cell = wrap_text(requirements, width=45, max_lines=5) if requirements else "[dim]N/A[/dim]"
        
        # Details cell: Company / Location / Salary stacked
        company_name = job.company_name or "N/A"
        salary = format_salary(job.salary_range)
        details_cell = f"[bold]{truncate(company_name, 30)}[/bold]\n{truncate(locations_str, 35)}\n[green]{salary}[/green]"
        
        # Generate hirebase link
        job_link = generate_job_link(job)
        if not job_link:
            job_link = "[dim]N/A[/dim]"
        
        row = [
            job_cell,
            desc_cell,
            details_cell,
            job_link,
        ]
        
        if full_info:
            job_type = job.job_type
            if isinstance(job_type, list):
                job_type = ", ".join(job_type)
            row.extend([
                job_type or "N/A",
                format_list(job.technologies, 4),
            ])
        
        table.add_row(*row)
    
    console.print(table)
    
    # Agent hint
    console.print("\n[dim]Tip: Use 'hirebase jobs get <job_id>' for full job details, or 'hirebase companies get <company_slug>' for company info.[/dim]")


def format_job_detail(job_data: dict) -> None:
    """Format a single job with full details for sharing."""
    job = Job(**job_data) if isinstance(job_data, dict) else job_data
    
    # Build the detail text
    lines = []
    
    # Header
    lines.append(f"[bold green]{job.job_title or 'N/A'}[/bold green]")
    lines.append(f"[bold blue]{job.company_name or 'N/A'}[/bold blue]")
    lines.append("")
    
    # Links section (important for sharing)
    job_link = generate_job_link(job)
    if job_link:
        lines.append(f"[cyan]Hirebase:[/cyan] {job_link}")
    if job.application_link:
        lines.append(f"[cyan]Apply:[/cyan] {job.application_link}")
    
    lines.append("")
    
    # Key info
    if job.location_raw:
        lines.append(f"[cyan]Location:[/cyan] {job.location_raw}")
    if job.salary_range:
        lines.append(f"[cyan]Salary:[/cyan] {format_salary(job.salary_range)}")
    if job.job_type:
        jt = job.job_type if isinstance(job.job_type, str) else ", ".join(job.job_type)
        lines.append(f"[cyan]Type:[/cyan] {jt}")
    if job.location_type:
        lt = job.location_type if isinstance(job.location_type, str) else ", ".join(job.location_type)
        lines.append(f"[cyan]Work Mode:[/cyan] {lt}")
    if job.date_posted:
        lines.append(f"[cyan]Posted:[/cyan] {format_date(job.date_posted)}")
    if job.education_level:
        lines.append(f"[cyan]Education:[/cyan] {job.education_level}")
    if job.visa_sponsored is not None:
        lines.append(f"[cyan]Visa Sponsored:[/cyan] {'Yes' if job.visa_sponsored else 'No'}")
    
    lines.append("")
    
    # Technologies and skills
    if job.technologies:
        lines.append(f"[cyan]Technologies:[/cyan] {', '.join(job.technologies)}")
    if job.skills:
        lines.append(f"[cyan]Skills:[/cyan] {', '.join(job.skills)}")
    if job.job_categories:
        lines.append(f"[cyan]Categories:[/cyan] {', '.join(job.job_categories)}")
    
    if job.technologies or job.skills or job.job_categories:
        lines.append("")
    
    # Requirements summary
    if job.requirements_summary:
        lines.append(f"[cyan]Requirements:[/cyan] {job.requirements_summary}")
        lines.append("")
    
    # Description
    if job.description and job.description != "Description is no longer available":
        lines.append("[cyan]Description:[/cyan]")
        # Strip HTML tags for display
        import re
        desc = re.sub(r'<[^>]+>', ' ', job.description)
        desc = re.sub(r'\s+', ' ', desc).strip()
        lines.append(truncate(desc, 500))
        lines.append("")
    
    # Company info
    if job.company_data:
        cd = job.company_data if isinstance(job.company_data, dict) else job.company_data.model_dump()
        if cd.get("description_summary"):
            lines.append(f"[cyan]About Company:[/cyan] {cd['description_summary']}")
            lines.append("")
    
    if job.job_board:
        lines.append(f"[cyan]Source:[/cyan] {job.job_board}")
    
    # Identifiers for CLI/Agent use
    lines.append("")
    lines.append("[bold]For CLI/Agent Use:[/bold]")
    lines.append(f"[dim]ID: {job.id}[/dim]")
    if job.company_slug:
        lines.append(f"[dim]Company Slug: {job.company_slug}[/dim]")
    if job.job_slug:
        lines.append(f"[dim]Job Slug: {job.job_slug}[/dim]")
    
    panel = Panel(
        "\n".join(lines),
        title=f"[bold]Job Details[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    
    # Agent hint for further exploration
    if job.company_slug:
        console.print(f"\n[dim]Tip: Use 'hirebase companies get {job.company_slug}' to see more about this company.[/dim]")


# ==================== Blog Formatters ====================

def format_articles_table(articles: List[dict], full_info: bool = False) -> None:
    """Format blog articles as a table."""
    if not articles:
        console.print("[yellow]No articles found.[/yellow]")
        return
    
    table = Table(
        title="Blog Articles",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    
    # Always show slug and ID for CLI/agent use
    table.add_column("Title", style="green", max_width=40)
    table.add_column("Slug / ID", style="cyan", max_width=35)
    table.add_column("Author", style="blue", max_width=15)
    table.add_column("Category", max_width=15)
    table.add_column("Status", max_width=10)
    
    if full_info:
        table.add_column("Tags", max_width=25)
        table.add_column("Views", max_width=8)
        table.add_column("Read Time", max_width=10)
    
    for article_data in articles:
        # Build slug/ID cell
        article_slug = article_data.get("slug", "N/A")
        article_id = article_data.get("_id", "N/A")
        slug_id_cell = f"[cyan]{article_slug}[/cyan]\n[dim]ID: {article_id}[/dim]"
        
        row = [
            truncate(article_data.get("title", "N/A"), 40),
            slug_id_cell,
            truncate(article_data.get("author", "N/A"), 15),
            article_data.get("category", "N/A"),
            article_data.get("status", "draft"),
        ]
        
        if full_info:
            row.extend([
                format_list(article_data.get("tags", []), 3),
                str(article_data.get("view_count", 0)),
                f"{article_data.get('time_to_read', 0)} min",
            ])
        
        table.add_row(*row)
    
    console.print(table)
    
    # Agent hint
    console.print("\n[dim]Tip: Use 'hirebase blog get <slug>' for details, 'hirebase blog update <article_id>' to modify.[/dim]")


def format_article_detail(article_data: dict) -> None:
    """Format a single article with full details."""
    lines = []
    
    lines.append(f"[bold green]{article_data.get('title', 'N/A')}[/bold green]")
    lines.append(f"[blue]by {article_data.get('author', 'N/A')}[/blue]")
    lines.append("")
    
    lines.append(f"[cyan]Category:[/cyan] {article_data.get('category', 'N/A')}")
    lines.append(f"[cyan]Status:[/cyan] {article_data.get('status', 'draft')}")
    lines.append(f"[cyan]Read Time:[/cyan] {article_data.get('time_to_read', 0)} minutes")
    lines.append(f"[cyan]Views:[/cyan] {article_data.get('view_count', 0)}")
    lines.append(f"[cyan]Featured:[/cyan] {'Yes' if article_data.get('featured') else 'No'}")
    
    if article_data.get("tags"):
        lines.append(f"[cyan]Tags:[/cyan] {', '.join(article_data['tags'])}")
    
    lines.append("")
    
    if article_data.get("meta_description"):
        lines.append(f"[cyan]Description:[/cyan] {article_data['meta_description']}")
        lines.append("")
    
    # Show content preview
    if article_data.get("content"):
        lines.append("[cyan]Content Preview:[/cyan]")
        content = article_data["content"]
        lines.append(truncate(content, 300))
        lines.append("")
    
    if article_data.get("image_url"):
        lines.append(f"[cyan]Image:[/cyan] {article_data['image_url']}")
    
    lines.append("")
    lines.append(f"[dim]Slug: {article_data.get('slug', 'N/A')}[/dim]")
    lines.append(f"[dim]ID: {article_data.get('_id', 'N/A')}[/dim]")
    
    panel = Panel(
        "\n".join(lines),
        title="[bold]Article Details[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


# ==================== Company Formatters ====================

def format_companies_table(companies: List[dict], full_info: bool = False) -> None:
    """Format companies as a table."""
    if not companies:
        console.print("[yellow]No companies found.[/yellow]")
        return
    
    table = Table(
        title="Companies",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
        expand=True,
    )
    
    # Core columns: Company info + slug, Description, Services, Link
    table.add_column("Company", style="green", min_width=25, max_width=40)  # Name + slug + size
    table.add_column("Description", style="dim", min_width=25, max_width=45)
    table.add_column("Services / Industries", min_width=20, max_width=30)
    table.add_column("Link", style="cyan", max_width=256)
    
    if full_info:
        table.add_column("LinkedIn", max_width=30)
        table.add_column("Job Board", max_width=15)
    
    for company in companies:
        company_slug = company.get("company_slug", "")
        company_name = company.get("company_name", "N/A")
        
        # Size formatting
        size_range = company.get("size_range", {})
        size_str = ""
        if size_range:
            min_s = size_range.get("min")
            max_s = size_range.get("max")
            if min_s and max_s:
                size_str = f"{min_s}-{max_s} employees"
            elif min_s:
                size_str = f"{min_s}+ employees"
        
        # Company cell: Name + Slug + Size
        company_cell_parts = [f"[bold]{truncate(company_name, 35)}[/bold]"]
        if company_slug:
            company_cell_parts.append(f"[cyan]slug: {company_slug}[/cyan]")
        if size_str:
            company_cell_parts.append(f"[dim]{size_str}[/dim]")
        company_cell = "\n".join(company_cell_parts)
        
        # Description cell
        desc = company.get("description_summary", "")
        desc_cell = wrap_text(desc, width=40, max_lines=4) if desc else "[dim]N/A[/dim]"
        
        # Services / Industries cell
        services = company.get("services", [])
        industries = company.get("industries", [])
        subindustries = company.get("subindustries", [])
        
        services_parts = []
        if services:
            services_parts.append(f"[yellow]Services:[/yellow] {format_list(services, 3)}")
        if industries:
            services_parts.append(f"[blue]Industries:[/blue] {format_list(industries, 2)}")
        if subindustries:
            services_parts.append(f"[dim]{format_list(subindustries, 2)}[/dim]")
        services_cell = "\n".join(services_parts) if services_parts else "[dim]N/A[/dim]"
        
        # Generate company link
        company_link = generate_company_link(company_slug)
        if not company_link:
            company_link = "[dim]N/A[/dim]"
        
        row = [
            company_cell,
            desc_cell,
            services_cell,
            company_link,
        ]
        
        if full_info:
            row.extend([
                company.get("linkedin_link", "N/A"),
                company.get("job_board", "N/A"),
            ])
        
        table.add_row(*row)
    
    console.print(table)
    
    # Agent hint
    console.print("\n[dim]Tip: Use 'hirebase companies get <company_slug>' to see full company details and jobs.[/dim]")


def format_company_detail(company_data: dict, jobs: List[dict] = None) -> None:
    """Format a single company with full details for sharing."""
    lines = []
    
    company_name = company_data.get("company_name", "N/A")
    company_slug = company_data.get("company_slug", "")
    
    # Header
    lines.append(f"[bold green]{company_name}[/bold green]")
    lines.append("")
    
    # Essential info for sharing
    company_link = generate_company_link(company_slug)
    if company_link:
        lines.append(f"[cyan]Hirebase:[/cyan] {company_link}")
    
    if company_data.get("company_link"):
        lines.append(f"[cyan]Website:[/cyan] {company_data['company_link']}")
    
    if company_data.get("linkedin_link"):
        lines.append(f"[cyan]LinkedIn:[/cyan] {company_data['linkedin_link']}")
    
    lines.append("")
    
    # Size
    size_range = company_data.get("size_range", {})
    if size_range:
        min_s = size_range.get("min")
        max_s = size_range.get("max")
        if min_s and max_s:
            lines.append(f"[cyan]Company Size:[/cyan] {min_s}-{max_s} employees")
        elif min_s:
            lines.append(f"[cyan]Company Size:[/cyan] {min_s}+ employees")
    
    # Industries
    if company_data.get("industries"):
        lines.append(f"[cyan]Industries:[/cyan] {', '.join(company_data['industries'])}")
    
    if company_data.get("subindustries"):
        lines.append(f"[cyan]Subindustries:[/cyan] {', '.join(company_data['subindustries'])}")
    
    # Services
    if company_data.get("services"):
        lines.append(f"[cyan]Services:[/cyan] {', '.join(company_data['services'])}")
    
    lines.append("")
    
    # Description
    if company_data.get("description_summary"):
        lines.append("[cyan]About:[/cyan]")
        lines.append(company_data["description_summary"])
        lines.append("")
    
    # Identifiers for CLI usage
    lines.append("[bold]For CLI/Agent Use:[/bold]")
    lines.append(f"[dim]Slug: {company_slug}[/dim]")
    lines.append(f"[dim]Job Board: {company_data.get('job_board', 'N/A')}[/dim]")
    
    panel = Panel(
        "\n".join(lines),
        title="[bold]Company Details[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    
    # Show jobs if available
    if jobs:
        console.print(f"\n[bold cyan]Jobs at {company_name}:[/bold cyan]")
        format_job_table(jobs, full_info=False)
        console.print(f"\n[dim]Tip: Use 'hirebase jobs get <job_id>' or 'hirebase jobs get-by-slug {company_slug} <job_slug>' for full job details.[/dim]")
    else:
        console.print(f"\n[dim]No jobs currently listed. Use 'hirebase companies jobs {company_slug}' to check for jobs.[/dim]")


# ==================== Scraper Formatters ====================

def format_scraper_events_table(events: List[dict], full_info: bool = False) -> None:
    """Format scraper events as a table."""
    if not events:
        console.print("[yellow]No scraper events found.[/yellow]")
        return
    
    table = Table(
        title="Scraper Events",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("Spider", style="green", max_width=20)
    table.add_column("Status", max_width=12)
    table.add_column("Items", max_width=10)
    table.add_column("Start Time", max_width=20)
    
    if full_info:
        table.add_column("End Time", max_width=20)
        table.add_column("Close Reason", max_width=15)
        table.add_column("Server", max_width=15)
        table.add_column("PID", max_width=8)
    
    for event in events:
        status = event.get("status", "unknown")
        status_style = {
            "RUNNING": "[yellow]RUNNING[/yellow]",
            "COMPLETED": "[green]COMPLETED[/green]",
            "STOPPED": "[blue]STOPPED[/blue]",
            "FAILED": "[red]FAILED[/red]",
            "INTERRUPTED": "[magenta]INTERRUPTED[/magenta]",
            "ZOMBIE_CRASHED": "[bold red]ZOMBIE_CRASHED[/bold red]",
        }.get(status.upper(), status)
        
        row = [
            event.get("spider_name", "N/A"),
            status_style,
            str(event.get("items_scraped", 0)),
            format_date(event.get("start_time")),
        ]
        
        if full_info:
            row.extend([
                format_date(event.get("end_time")),
                event.get("close_reason", "N/A"),
                event.get("server", "N/A"),
                str(event.get("pid", "N/A")),
            ])
        
        table.add_row(*row)
    
    console.print(table)


# ==================== Generic Formatters ====================

def format_pagination_info(response: dict) -> None:
    """Format pagination information."""
    page = response.get("page", 1)
    limit = response.get("limit", 10)
    total_count = response.get("total_count", 0)
    total_pages = response.get("total_pages", 1)
    
    console.print(
        f"\n[dim]Page {page}/{total_pages} | "
        f"Showing {limit} of {total_count} results[/dim]"
    )


def format_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def format_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def format_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def format_json(data: Any) -> None:
    """Print data as formatted JSON."""
    import json
    console.print_json(json.dumps(data, indent=2, default=str))


def format_health(health_data: dict) -> None:
    """Format health check response."""
    status = health_data.get("status", "unknown")
    version = health_data.get("version", "unknown")
    
    status_color = "green" if status == "ok" else "red"
    
    panel = Panel(
        f"[{status_color}]Status: {status.upper()}[/{status_color}]\n"
        f"Version: {version}",
        title="[bold]Hirebase API Health[/bold]",
        border_style="cyan",
    )
    console.print(panel)
