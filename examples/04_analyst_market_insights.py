#!/usr/bin/env python3
"""Market analysts: KPIs and distributions for a filtered job cohort."""

from _common import banner, marker, require_api_key, step

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Analyst — cohort insights",
        "Market analysts & researchers",
        "Headline KPIs, salary stats, and top skills for any search-shaped cohort.",
    )

    client = hirebase.Client()

    cohort = {
        "job_titles": ["Data Scientist", "Machine Learning Engineer"],
        "location_types": ["Remote"],
        "geo_locations": [
            {"country": "United States"},
        ],
        "days_ago": 30,
        "hide_recruiting_agencies": 'true',
    }

    step(1, "POST /v2/jobs/insights (same filters as job search)")
    marker("REQUEST", "Aggregates up to 500 freshest matching jobs")
    insights = client.jobs.insights(cohort)

    h = insights.headline
    step(2, "Headline KPIs")
    marker("HEADLINE", "Executive summary strip")
    print(f"    Total cohort size (index): {h.total_count:,}")
    print(f"    Sample analyzed:         {h.sample_size:,}")
    print(f"    Median salary (US):      ${h.median_salary:,.0f}" if h.median_salary else "    Median salary:           n/a")
    print(f"    % remote:                {h.pct_remote:.1f}%")
    print(f"    Top hiring company:      {h.top_company or '—'}")
    print(f"    Top technology:          {h.top_technology or '—'}")
    print(f"    New this week:           {h.new_this_week:,}")

    s = insights.salary
    step(3, "Salary distribution")
    marker("SALARY", f"n={s.count} | p25={s.p25} p50={s.p50} p75={s.p75}")
    if s.histogram:
        top_bins = sorted(s.histogram, key=lambda b: b.count, reverse=True)[:3]
        for b in top_bins:
            print(f"    ${b.lower:,.0f}–${b.upper:,.0f}: {b.count} jobs")

    step(4, "Top technologies & locations")
    marker("TOP TECH", "Most common technologies in cohort")
    for item in insights.top_technologies[:8]:
        print(f"    • {item['key']}: {item['count']} ({item.get('percent', 0):.1f}%)")
    marker("TOP LOCATIONS", "Hottest locations")
    for item in insights.top_locations[:5]:
        print(f"    • {item.get('label', item)}: {item['count']}")

    marker("DONE", "Feed insights into dashboards, reports, or slide decks.")
    client.close()


if __name__ == "__main__":
    main()
