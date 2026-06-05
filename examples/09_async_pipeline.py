#!/usr/bin/env python3
"""Platform engineers: non-blocking I/O with AsyncClient."""

import asyncio

from _common import banner, marker, print_job_row, require_api_key, step

import hirebase


async def main() -> None:
    require_api_key()
    banner(
        "Async pipeline",
        "Platform & backend engineers",
        "Same search + neural flows with httpx — fits FastAPI, workers, notebooks.",
    )

    async with hirebase.AsyncClient() as client:
        step(1, "await client.jobs.search(...)")
        marker("ASYNC SEARCH", "Non-blocking lexical search")
        result = await client.jobs.search(
            {"job_titles": ["Platform Engineer"], "location_types": ["Remote"], "limit": 3}
        )
        for job in result:
            print_job_row(job)

        step(2, "await client.jobs.neural_search(...)")
        marker("ASYNC NEURAL", "Semantic query + filters")
        neural = await client.jobs.neural_search(
            text="kubernetes platform engineer infrastructure",
            lexical={"location_types": ["Remote"], "geo_locations": [{"country": "United States"}], "limit": 3},
        )
        for job in neural:
            print_job_row(job, show_score=True)

        step(3, "await client.companies.search(...)")
        marker("ASYNC COMPANIES", "Company discovery")
        cos = await client.companies.search(
            {"keywords": ["infrastructure"], "limit": 3}
        )
        for c in cos:
            print(f"    • {c.company_name} ({c.company_slug})")

    marker("DONE", "Use async with asyncio.gather for parallel cohort fetches.")


if __name__ == "__main__":
    asyncio.run(main())
