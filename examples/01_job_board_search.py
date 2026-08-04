#!/usr/bin/env python3
"""Job board integrators: power a search results page with lexical filters."""

from _common import (
    banner,
    marker,
    print_job_row,
    require_api_key,
    step,
)

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Job board — lexical search",
        "Job board developers",
        "Build a traditional job search UI: titles, location, remote, pagination.",
    )

    client = hirebase.Client()

    query = {
        "job_titles": ["Software Engineer", "Backend Engineer"],
        "location_types": ["Remote", "Hybrid"],
        "geo_locations": [
            {"city": "San Francisco", "region": "California", "country": "United States"}
        ],
        "days_ago": 30,
        "limit": 100,
        "page": 1,
    }

    step(1, "POST /v2/jobs/search with typed filters")
    marker("REQUEST", "job_titles + geo_locations + location_types + days_ago")
    result = client.jobs.search(query)

    step(2, "Render results (JobSearchResult is iterable)")
    marker(
        "RESULT",
        f"{result.total_count:,} total matches | page {result.page}/{result.total_pages}",
    )
    for job in result:
        print_job_row(job)

    step(3, "Fetch one job by id for a detail page")
    if result.jobs:
        job_id = result.jobs[0].id
        marker("GET JOB", f"/v2/jobs/{job_id}")
        detail = client.jobs.get(job_id)
        print(f"    Full description length: {len(detail.description or '')} chars")
        print(f"    Technologies: {(detail.technologies or [])[:6]}")

    marker("DONE", "Wire this into your job board search + detail routes.")
    client.close()


if __name__ == "__main__":
    main()
