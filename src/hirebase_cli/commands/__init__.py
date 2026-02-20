"""CLI commands for Hirebase."""

from .jobs import app as jobs_app
from .blog import app as blog_app
from .companies import app as companies_app
from .scraper import app as scraper_app
from .health import app as health_app
from .insights import app as insights_app

__all__ = ["jobs_app", "blog_app", "companies_app", "scraper_app", "health_app", "insights_app"]
