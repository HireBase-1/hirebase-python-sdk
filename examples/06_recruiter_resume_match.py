#!/usr/bin/env python3
"""Recruiters: upload a resume, parse it, find matching open roles."""

from _common import (
    banner,
    fetch_sample_resume,
    marker,
    print_job_row,
    require_api_key,
    step,
)

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Recruiter — resume → job matches",
        "Recruiters & talent teams",
        "Public flow: resume stored on Hirebase, parsed, then neural search by resume id.",
    )

    client = hirebase.Client()
    pdf_bytes = fetch_sample_resume()

    step(1, "Upload + parse resume (one call)")
    marker("REQUEST", "POST /v2/resumes/upload/ then POST /v2/resumes/{id}/parse")
    resume = client.resumes.upload_and_parse(pdf_bytes)
    print(f"    Resume id: {resume.id}")
    print(f"    Status:    {resume.status}")
    if resume.parsed_data:
        pi = resume.parsed_data.get("personal_information", {})
        if isinstance(pi, dict):
            data = pi.get("data") or pi
            if isinstance(data, dict) and data.get("full_name"):
                print(f"    Parsed name: {data.get('full_name')}")

    step(2, "Neural search using resume as the vector signal")
    marker("REQUEST", "POST /v2/jobs/neural-search with artifact_id = resume id")
    matches = client.jobs.neural_search(
        resume_id=resume.id,
        lexical={
            "location_types": ["Remote", "Hybrid"],
            "days_ago": 30,
            "limit": 8,
        },
    )
    marker("RESULT", f"{matches.total_count:,} jobs in cohort | showing page")
    for job in matches:
        print_job_row(job, show_score=True)

    step(3, "Tighten with lexical-only filters on top of resume signal")
    marker("TIP", "Combine resume_id with job_titles for role-specific shortlists")
    focused = client.jobs.neural_search(
        resume_id=resume.id,
        lexical={
            "job_titles": ["Software Engineer", "Machine Learning Engineer"],
            "limit": 5,
        },
    )
    for job in focused:
        print_job_row(job, show_score=True)

    marker("DONE", "Use resume_id in your ATS ↔ Hirebase matching integration.")
    client.close()


if __name__ == "__main__":
    main()
