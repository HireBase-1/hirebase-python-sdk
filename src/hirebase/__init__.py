"""Hirebase Python SDK.

A lean, typed client for the Hirebase public API (https://api.hirebase.org).

Quickstart:

    import hirebase

    client = hirebase.Client(api_key="sk_live_...")

    # Search jobs (typed results by default)
    result = client.jobs.search({
        "job_titles": ["Software Engineer", "Product Engineer"],
        "locations": [{"city": "San Francisco", "region": "California",
                       "country": "United States"}],
    })
    for job in result:
        print(job.job_title, job.company_name)

    # Async usage
    client = hirebase.AsyncClient(api_key="sk_live_...")
    task = await client.jobs.export(query, format="json")
    success, result = await client.tasks.poll(task)
    if success:
        await client.stream_file(result["download_url"], file_path="jobs.json")
        for job in client.jobs.stream_file("jobs.json"):
            ...
"""

from ._version import __version__
from .client import AsyncClient, Client
from .config import DEFAULT_BASE_URL, Settings
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    HirebaseError,
    NotFoundError,
    PaymentRequiredError,
    PermissionError_,
    RateLimitError,
    ServerError,
    TaskError,
    TaskFailed,
    TaskTimeout,
)
from .models import (
    Company,
    CompanyQuery,
    CompanySearchResult,
    Job,
    JobInsights,
    JobQuery,
    JobSearchResult,
    Location,
    SalaryRange,
    Task,
    TaskState,
    YoeRange,
)

__all__ = [
    "__version__",
    "Client",
    "AsyncClient",
    "Settings",
    "DEFAULT_BASE_URL",
    # Models
    "Job",
    "JobQuery",
    "JobSearchResult",
    "Company",
    "CompanyQuery",
    "CompanySearchResult",
    "Task",
    "TaskState",
    "JobInsights",
    "Location",
    "SalaryRange",
    "YoeRange",
    # Exceptions
    "HirebaseError",
    "ConfigurationError",
    "APIError",
    "AuthenticationError",
    "PermissionError_",
    "PaymentRequiredError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TaskError",
    "TaskFailed",
    "TaskTimeout",
]
