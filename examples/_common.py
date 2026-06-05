"""Shared helpers for runnable SDK examples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running examples before `pip install -e .`
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

SAMPLE_RESUME_URL = "https://pjreddie.com/static/resume.pdf"


def load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(_ROOT / ".env")
    except ImportError:
        pass


def require_api_key() -> None:
    load_env()
    if not os.getenv("HIREBASE_API_KEY"):
        print(
            "Set HIREBASE_API_KEY in your environment or in hirebase-python-sdk/.env"
        )
        sys.exit(1)


def banner(title: str, audience: str, description: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print(f"  Audience: {audience}")
    print(f"  {description}")
    print("=" * 72)


def marker(label: str, detail: str = "") -> None:
    print(f"\n>>> [{label}]")
    if detail:
        print(f"    {detail}")


def step(number: int, message: str) -> None:
    print(f"\n--- Step {number}: {message} ---")


def fetch_sample_resume() -> bytes:
    """Download the public sample resume (PJ Reddie) used across examples."""
    import httpx

    marker("FETCH RESUME", SAMPLE_RESUME_URL)
    response = httpx.get(SAMPLE_RESUME_URL, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    print(f"    Downloaded {len(response.content):,} bytes")
    return response.content


def print_job_row(job, *, show_score: bool = False) -> None:
    salary = job.salary_range
    sal = ""
    if salary and (salary.min or salary.max):
        sal = f" | ${salary.min or '?'}-${salary.max or '?'}"
    score = ""
    if show_score and getattr(job, "vector_score", None) is not None:
        score = f" | similarity={job.vector_score:.2f}"
    loc = job.location_raw or (str(job.locations[0]) if job.locations else "")
    print(f"    • {job.job_title} @ {job.company_name}{sal}{score}")
    if loc:
        print(f"      {loc}")


def print_company_row(company) -> None:
    industries = ", ".join((company.industries or [])[:2]) or "—"
    print(f"    • {company.company_name} ({company.company_slug}) — {industries}")
