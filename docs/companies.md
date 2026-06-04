# Companies

The `client.companies` resource covers company search, fetching a company
profile (optionally with its jobs and insights), paginating a company's jobs,
and company-scoped market insights.

All examples use a sync client; every method exists on `AsyncClient` with the
same signature (just `await` it).

```python
import hirebase
client = hirebase.Client(api_key="sk_live_...")
```

---

## `companies.search(query=None, *, page=None, limit=None, return_type=None)`

Search companies. Returns a `CompanySearchResult` (iterable, indexable).

```python
result = client.companies.search({
    "company_name": "Stripe",
    "industries": ["Tech, Software & IT Services"],
    "limit": 10,
})

print(result.total_count)
for company in result:
    print(company.company_name, "—", company.company_slug)
    print("  ", company.description_summary)
```

### Typed query objects

Pass a `dict` or build a `CompanyQuery`. Unknown keys pass through.

```python
from hirebase import CompanyQuery

query = CompanyQuery(
    keywords=["AI", "remote"],
    industries=["Tech, Software & IT Services"],
    company_types=["11-50", "51-200"],   # size buckets
    sort_by="clout",
    sort_order="desc",
)
result = client.companies.search(query)
```

### Common filter fields

| Field | Type | Notes |
|---|---|---|
| `company_name` | `str` | Matches name + aliases |
| `keywords` | `list[str]` | Each term must hit description/services/industries |
| `query` | `str` | Free-text (back-compat single keyword) |
| `company_link` | `str` | Website/domain filter |
| `linkedin_link` | `str` | Full URL or slug |
| `industries` / `subindustries` | `list[str]` | Taxonomy |
| `company_types` | `list[str]` | Size buckets, e.g. `"1-10"`; alias `company_sizes` |
| `types` | `list[str]` | `Startup`, `Enterprise`, `Non-Profit`, ... |
| `hq_geolocations` | `list[Location]` | HQ location filter |
| `funding_types` | `list[str]` | e.g. `"Series A"` |
| `hide_recruiter_agencies` | `bool` | Defaults to true server-side |
| `sort_by` | `str` | `hottest`, `relevance`, `clout`, `rated`, `size`, `newest` |
| `page` / `limit` | `int` | Pagination (limit 1–100) |

---

## `companies.get(slug, *, return_jobs=True, return_insights=False, return_type=None)`

Fetch a company by slug. Returns a `Company`.

```python
company = client.companies.get("stripe")
print(company.company_name, company.founded, company.headquarters)
print(company.industries, company.size_range)

# Jobs returned alongside the profile (when return_jobs=True, the default)
for job in company.jobs or []:
    print(job.job_title)
```

Set `return_insights=True` to also fetch live insights in the same call (one
extra request). They're attached at `company.insights_data`:

```python
company = client.companies.get("stripe", return_jobs=True, return_insights=True)
print(company.insights_data.headline.total_count)
print(company.insights_data.salary.p50)
```

With `return_type=dict`, the raw payload is returned and insights (if requested)
are placed under the `"insights"` key.

### Bound helpers

A `Company` fetched through the client remembers it, so you can chain
follow-ups without repeating the slug:

```python
company = client.companies.get("stripe")

insights = company.insights()              # company-scoped insights
insights = company.insights(query={"days_ago": 30})

more_jobs = company.get_jobs(limit=25, sort_by="date_posted")
```

On an async client these helpers return awaitables:

```python
company = await async_client.companies.get("stripe")
insights = await company.insights()
```

---

## `companies.jobs(company, *, page=None, limit=None, sort_by=None, sort_order=None, job_board=None, job_category=None, return_type=None)`

Paginate a company's jobs. `company` may be a `Company`, a company dict, or a
slug string. Returns a `JobSearchResult`.

```python
jobs = client.companies.jobs("stripe", limit=25, sort_by="date_posted")
print(jobs.total_count)
for job in jobs:
    print(job.job_title)

# Filter to a board or category
backend = client.companies.jobs("stripe", job_category="Software Engineer")
greenhouse = client.companies.jobs("stripe", job_board="Greenhouse")
```

---

## `companies.insights(company, *, query=None, return_type=None)`

Live insights for jobs at a company. `company` may be a `Company`, dict, or
slug. `query` (a job-search filter) further scopes the cohort; the company slug
always wins.

```python
insights = client.companies.insights("stripe")
insights = client.companies.insights("stripe", query={"location_types": ["Remote"]})

print(insights.headline.median_salary)
print(insights.top_technologies[:5])
```

The return type is `JobInsights` — the same shape documented in
[Jobs](./jobs.md) under "insights".

---

## See also

- [Jobs](./jobs.md) — job search, the `JobQuery` filter, and `JobInsights`
- [Tasks](./tasks.md) — for company-scoped data exports (via `jobs.export`)
