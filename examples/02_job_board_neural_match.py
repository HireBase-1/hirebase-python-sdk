#!/usr/bin/env python3
"""Job board integrators: semantic 'jobs like this query' with lexical guardrails."""

from _common import banner, marker, print_job_row, require_api_key, step

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Job board — neural (hybrid) search",
        "Job board developers",
        "Semantic matching plus filters — great for 'describe the role' search boxes.",
    )

    client = hirebase.Client()

    step(1, "POST /v2/jobs/neural-search")
    marker(
        "VECTOR",
        "Natural-language query encoded to a 768-d embedding",
    )
    marker(
        "LEXICAL",
        "Same filters as classic search (remote, experience, recency)",
    )

    result = client.jobs.neural_search(
        text="senior backend engineer building APIs with Python and distributed systems",
        lexical={
            "location_types": ["Remote", "Hybrid"],
            "experience": ["Senior"],
            "days_ago": 45,
            "limit": 5,
        },
    )

    step(2, "Ranked jobs with vector_score")
    marker(
        "RESULT",
        f"{result.total_count:,} matches — sorted by combined lexical + semantic rank",
    )
    for job in result:
        print_job_row(job, show_score=True)

    job_cond = result.jobs[0]
    company_slug = job_cond.company_slug
    job_slug = job_cond.job_slug

    print('\n')
    step(3, "Find jobs similar to a known posting:")
    print_job_row(job_cond, show_score=True)

    marker("VECTOR", "Resolve slug → job id, then similarity search")
    similar = client.jobs.neural_search(
        company_slug=company_slug,
        job_slug=job_slug,
        lexical={"limit": 3},
    )
    for job in similar:
        print_job_row(job, show_score=True)

    marker("DONE", "Expose neural search as an optional 'smart search' mode in your UI.")
    client.close()


if __name__ == "__main__":
    main()
