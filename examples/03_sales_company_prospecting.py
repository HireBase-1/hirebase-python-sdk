#!/usr/bin/env python3
"""Sales / GTM: company research for GPU rentals — tech & skills signals, not job search."""

from _common import banner, marker, print_company_row, require_api_key, step

import hirebase

# Company-discovery filters: who is building LLMs, gen media, agents, etc.
NICHE_KEYWORDS = [
    "large language models",
    "LLMs",
    "generative AI",
    "image generation",
    "computer vision",
    "speech recognition",
    "AI agents",
    "autonomous agents",
    "recommendation system",
    "model training",
    "deep learning",
    "foundation model",
]
MAX_PROSPECTS = 5
INSIGHTS_WINDOW_DAYS = 90


def _format_ranked_items(items, *, limit: int = 6) -> str:
    if not items:
        return "—"
    return ", ".join(
        f"{row['key']} ({row.get('percent', row.get('count', ''))}"
        f"{'%' if 'percent' in row else ''})"
        for row in items[:limit]
    )


def print_company_research(name: str, slug: str, insights, *, profile=None) -> None:
    """What the company is building toward — inferred from technologies & skills in listings."""
    marker("COMPANY RESEARCH", f"{name} ({slug})")
    if profile:
        if profile.description_summary:
            print(f"    About:          {profile.description_summary[:240]}...")
        if profile.industries:
            print(f"    Industries:     {', '.join(profile.industries[:3])}")
        if profile.founded:
            print(f"    Founded:        {profile.founded}")

    h = insights.headline
    if h.top_technology:
        print(f"    Lead technology:  {h.top_technology}")

    marker("TECHNOLOGIES SOUGHT", "From aggregated public listings (company insights)")
    print(f"    {_format_ranked_items(insights.top_technologies)}")

    marker("SKILLS SOUGHT", "Capabilities the company is investing in")
    print(f"    {_format_ranked_items(insights.top_skills)}")

    if insights.top_locations:
        locs = ", ".join(
            item.get("label", item.get("key", str(item)))[:40]
            for item in insights.top_locations[:3]
        )
        print(f"    Primary locations: {locs or '—'}")


def print_outreach_card(
    rank: int, name: str, slug: str, insights, profile=None
) -> None:
    """CRM-ready snapshot — example account for outbound."""
    techs = [t["key"] for t in (insights.top_technologies or [])[:3]]
    skills = [s["key"] for s in (insights.top_skills or [])[:3]]
    tech_str = ", ".join(techs) if techs else "—"
    skill_str = ", ".join(skills) if skills else "—"
    hook = (
        f"Building in {insights.headline.top_technology or techs[0] if techs else 'ML'} — "
        f"pitch GPU rentals aligned to {tech_str.split(',')[0] if techs else 'their stack'}."
    )
    print(f"    [{rank}] {name}")
    print(f"        slug:       {slug}")
    if profile and profile.company_link:
        print(f"        website:    {profile.company_link}")
    print(f"        technologies: {tech_str}")
    print(f"        skills:       {skill_str}")
    print(f"        outreach:     {hook}")


def main() -> None:
    require_api_key()
    banner(
        "Sales — company research for compute providers",
        "Sales & GTM (GPU / cloud hardware)",
        "Discover model-building companies, research technologies & skills they seek "
        "via company insights — no job search, no recruiting workflow.",
    )

    client = hirebase.Client()

    step(1, "ICP: companies building LLMs, gen media, agents, and other models")
    marker(
        "USE CASE",
        "Company research before outreach — understand stack and skill demand, "
        "then sell GPU rentals, reserved clusters, or inference capacity.",
    )
    marker("DISCOVERY KEYWORDS", f"{len(NICHE_KEYWORDS)} product & stack terms")
    for kw in NICHE_KEYWORDS:
        print(f"      • {kw}")

    step(2, "Find companies in the niche")
    marker("REQUEST", "POST /v2/hirebase/companies/search")
    companies = client.companies.search(
        {
            "keywords": NICHE_KEYWORDS,
            "hide_recruiter_agencies": True,
            "limit": MAX_PROSPECTS,
        }
    )
    marker("RESULT", f"{companies.total_count:,} companies in index match filters")
    for company in companies:
        print_company_row(company)

    if not companies.companies:
        marker("SKIP", "No companies returned — try broadening keywords.")
        client.close()
        return

    step(3, "Research each company — technologies & skills from listings")
    marker(
        "REQUEST",
        "POST /v2/hirebase/companies/{slug}/insights (aggregates their public listings)",
    )
    researched = []
    for company in companies.companies:
        slug = company.company_slug
        name = company.company_name
        profile = client.companies.get(slug, return_jobs=False)
        insights = client.companies.insights(
            slug,
            query={"days_ago": INSIGHTS_WINDOW_DAYS},
        )
        print_company_research(name, slug, insights, profile=profile)
        researched.append((name, slug, insights, profile))

    step(4, "Example companies for outreach")
    marker(
        "OUTREACH TARGETS",
        f"{len(researched)} accounts from this search — copy into CRM or sequences",
    )
    for rank, (name, slug, insights, profile) in enumerate(researched, start=1):
        print_outreach_card(rank, name, slug, insights, profile)

    marker(
        "DONE",
        "Repeat with different keyword sets (e.g. robotics, biotech ML) to build "
        "territory lists; insights reflect what companies seek in listings, not a job feed.",
    )
    client.close()


if __name__ == "__main__":
    main()
