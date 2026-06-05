#!/usr/bin/env python3
"""Competitive intel: how a specific company is hiring (insights + roles)."""

from _common import banner, marker, print_job_row, require_api_key, step

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Competitive intel — company hiring pulse",
        "Strategy, corp dev, competitive intelligence",
        "Insights scoped to one employer + live job list.",
    )

    client = hirebase.Client()
    company_slug = "openai"  # change to any slug you care about

    step(1, f"Find the company: '{company_slug}'")
    marker("REQUEST", "POST /v2/hirebase/companies/search")
    hits = client.companies.search({"company_name": "OpenAI", "limit": 3})
    if hits.companies:
        company_slug = hits.companies[0].company_slug
        marker("MATCH", f"Using slug: {company_slug}")
    else:
        marker("FALLBACK", f"Using default slug: {company_slug}")

    step(2, "Company-scoped insights")
    marker("REQUEST", f"POST /v2/hirebase/companies/{company_slug}/insights")
    insights = client.companies.insights(
        company_slug,
        query={"days_ago": 90},
    )
    h = insights.headline
    marker("INSIGHTS", f"Sample of {h.sample_size} jobs at this company")
    print(f"    Median salary:  ${h.median_salary:,.0f}" if h.median_salary else "    Median salary:  n/a")
    print(f"    % remote:       {h.pct_remote:.1f}%")
    print(f"    Dominant level: {h.dominant_experience_level or '—'}")
    print(f"    New this week:  {h.new_this_week}")

    marker("TOP TECH AT COMPANY")
    for item in insights.top_technologies[:6]:
        print(f"    • {item['key']}: {item['count']}")

    step(3, "Profile + optional bundled insights")
    marker("REQUEST", f"GET /v2/hirebase/companies/{company_slug}?return_insights=True")
    profile = client.companies.get(company_slug, return_jobs=True, return_insights=True)
    print(f"    {profile.company_name}")
    if profile.founded:
        print(f"    Founded: {profile.founded}")
    if profile.industries:
        print(f"    Industries: {', '.join(profile.industries[:3])}")

    step(4, "Recent openings")
    marker("JOBS", "Latest postings at this company")
    for job in (profile.jobs or [])[:6]:
        print_job_row(job)

    marker("DONE", "Track hiring mix, comp, and tech stack shifts quarter over quarter.")
    client.close()


if __name__ == "__main__":
    main()
