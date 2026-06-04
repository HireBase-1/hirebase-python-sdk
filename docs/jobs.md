# Jobs

The `client.jobs` resource covers everything about job postings: live search,
fetching a single job, market insights, and bulk exports + streaming.

All examples use a sync client; every method exists on `AsyncClient` with the
same signature (just `await` it).

```python
import hirebase
client = hirebase.Client(api_key="sk_live_...")
```

---

## `jobs.search(query=None, *, page=None, limit=None, return_type=None)`

Search jobs with filters. Returns a `JobSearchResult` (iterable, indexable).

```python
result = client.jobs.search({
    "job_titles": ["Software Engineer", "Product Engineer"],
    "locations": [{"city": "San Francisco", "region": "California",
                   "country": "United States"}],
    "location_types": ["Remote", "Hybrid"],
    "limit": 20,
})

print(result.total_count)   # total matches across all pages
print(result.total_pages)
for job in result:          # iterate the current page
    print(job.job_title, "@", job.company_name, "—", job.salary_range)
```

`page` and `limit` can be passed as keyword arguments and override anything in
the query body:

```python
page_2 = client.jobs.search(query, page=2, limit=50)
```

### Typed query objects

You can pass a plain `dict` or build a typed `JobQuery`. Booleans are accepted
natively and converted to the API's `"true"` convention; unknown keys pass
through untouched.

```python
from hirebase import JobQuery, SalaryRange, YoeRange

query = JobQuery(
    job_titles=["Backend Engineer"],
    keywords=["python", "kubernetes"],
    salary=SalaryRange(min=150_000, currency="USD"),
    yoe=YoeRange(min=3, max=8),
    location_types=["Remote"],
    visa=True,
    sort_by="date_posted",
    sort_order="desc",
)
result = client.jobs.search(query)
```

### Common filter fields

| Field | Type | Notes |
|---|---|---|
| `job_titles` | `list[str]` | Titles to match |
| `keywords` | `list[str]` | Match in title/description/skills/tech |
| `company_names` | `str \| list[str]` | Exact company name(s); alias `company_name` |
| `company_slugs` | `str \| list[str]` | Hirebase company slug(s); alias `company_slug` |
| `geo_locations` | `list[Location]` | **Alias: `locations`** — `{city, region, country}` |
| `location_group` | `str` | Predefined group, e.g. `"Bay_Area"` |
| `location_types` | `list[str]` | `Remote`, `Hybrid`, `On-site` |
| `experience` | `list[str]` | YOE bands: `Entry`, `Mid`, `Senior`, ... |
| `yoe` | `YoeRange` | `{min, max}` years |
| `salary` | `SalaryRange` | `{min, max, currency}` |
| `currency` | `str` | e.g. `"USD"` |
| `job_types` | `list[str]` | `Full-time`, `Contract`, ... |
| `industry` / `sub_industry` | `str \| list[str]` | Taxonomy filters |
| `days_ago` | `int` | Posted within N days |
| `date_posted` | `str` | e.g. `"2025-12-01"` |
| `visa` | `bool` | Only visa-sponsoring jobs |
| `include_expired` | `bool` | Include expired postings |
| `hide_recruiting_agencies` | `bool` | Drop agency listings |
| `sort_by` | `str` | `relevance`, `date_posted`, `salary`, ... |
| `page` / `limit` | `int` | Pagination |

---

## `jobs.get(job_id, *, return_type=None)`

Fetch a single job by its id. Returns a `Job`.

```python
job = client.jobs.get("6958cfd211e2763c3491ef8b")
print(job.job_title, job.description)
print(job.technologies, job.skills, job.benefits)
print(job.salary_range, job.yoe_range, job.experience_level)
```

Jobs also carry Hirebase scores when available: `compensation_value_score`,
`growth_score`, `prestige_score`, `flexibility_score`, etc.

---

## `jobs.insights(query=None, *, return_type=None)`

Live, search-driven market insights for the cohort matching `query` (accepts the
same filter shape as `search`). Returns a `JobInsights`.

```python
insights = client.jobs.insights({"job_titles": ["Data Scientist"],
                                  "location_types": ["Remote"]})

h = insights.headline
print(h.total_count, h.median_salary, h.pct_remote, h.top_company)

s = insights.salary
print(s.p25, s.p50, s.p75, s.p90, s.currency)
for b in s.histogram:
    print(b.lower, b.upper, b.count)

print(insights.top_technologies[:5])
print(insights.top_companies[:5])
```

`JobInsights` types the `headline` and `salary` blocks; the many split/top-N
lists (e.g. `top_skills`, `industry_split`, `level_breakdown`) are lists of
dicts, and new sections are preserved automatically.

---

## Exporting jobs

Exports run as a server-side [task](./tasks.md) and produce a downloadable file.

### `jobs.export(query=None, *, format="json")` → `Task`

```python
task = client.jobs.export(query, format="json")   # or format="csv"

# Poll until done -> (success, result)
success, result = client.tasks.poll(task)
if not success:
    raise RuntimeError(f"Export failed: {result.error}")

# result is a dict with: download_url, file_size, record_count, expiry_time
client.stream_file(result["download_url"], file_path="./jobs.json")
```

See [Tasks](./tasks.md) for polling options (`interval`, `timeout`,
`on_progress`).

### Downloading: `client.stream_file(url, *, file_path)`

Streams a URL to disk without buffering the whole body. Returns the path.

```python
client.stream_file(result["download_url"], file_path="./exports/jobs.json")
```

---

## Streaming jobs (constant memory)

### `jobs.stream_file(path, *, return_type=None, format=None)`

Stream jobs out of a local export file — JSON Lines, a JSON array, or CSV.
Format is detected from the extension; override with `format="csv"` etc.

```python
# Typed Job objects (default)
for job in client.jobs.stream_file("./jobs.json"):
    print(job.job_title)

# Raw dicts
for row in client.jobs.stream_file("./jobs.json", return_type=dict):
    ...
```

> JSON **array** exports require the optional `ijson` dependency
> (`pip install "hirebase[streaming]"`). JSON Lines and CSV need nothing extra.

### `jobs.stream_url(url, *, return_type=None)`

Stream jobs **directly from the export URL** without saving to disk (JSON Lines
exports only).

```python
for job in client.jobs.stream_url(result["download_url"]):
    print(job.job_title)
```

On the async client, `stream_url` is an async generator:

```python
async for job in async_client.jobs.stream_url(url):
    ...
```

---

## See also

- [Tasks](./tasks.md) — polling the export task to completion
- [Companies](./companies.md) — company-scoped jobs and insights
