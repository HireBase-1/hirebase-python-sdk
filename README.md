# Hirebase Python SDK

A lean, typed Python client for the [Hirebase API](https://docs.hirebase.org/) —
search jobs and companies, run market insights, and export job data at scale.

- **Sync and async** clients (`hirebase.Client` / `hirebase.AsyncClient`).
- **Typed by default** — responses come back as Pydantic models; pass
  `return_type=dict` anywhere for raw dicts.
- **Streaming exports** — kick off an export, poll it, download it, and stream
  millions of jobs without loading them into memory.
- **Self-contained** — the SDK ships its own types and depends only on
  `requests`, `httpx`, and `pydantic`.

## Installation

```bash
pip install hirebase

# Optional extras
pip install "hirebase[streaming]"   # ijson, for streaming JSON-array exports
pip install "hirebase[cli]"         # the bundled `hirebase` command-line tool
```

## Authentication

Pass your API key directly, or set it via the environment:

```python
import hirebase
client = hirebase.Client(api_key="sk_live_...")
```

```bash
export HIREBASE_API_KEY="sk_live_..."
export HIREBASE_BASE_URL="https://api.hirebase.org"   # optional, this is the default
```

Resolution order for every setting is **argument → environment variable →
default**. The base URL defaults to `https://api.hirebase.org`.

## Quickstart

```python
import hirebase

client = hirebase.Client(api_key="sk_live_...")

# Search jobs — results are typed and iterable
result = client.jobs.search({
    "job_titles": ["Software Engineer", "Product Engineer"],
    "locations": [{"city": "San Francisco", "region": "California",
                   "country": "United States"}],
    "limit": 20,
})

print(result.total_count, "matches")
for job in result:
    print(job.job_title, "@", job.company_name, "—", job.salary_range)
```

Booleans are accepted natively (`visa=True`), and `locations` is a friendly
alias for the API's `geo_locations`. Unknown filter keys are passed through
untouched, so new API features work before the SDK is updated.

### Async

```python
import asyncio, hirebase

async def main():
    async with hirebase.AsyncClient(api_key="sk_live_...") as client:
        result = await client.jobs.search({"job_titles": ["Engineer"]})
        for job in result:
            print(job.job_title)

asyncio.run(main())
```

Every method has the same signature on both clients — the async versions are
awaitable.

## Jobs

```python
# Search
result = client.jobs.search(query, page=1, limit=20)

# Fetch one job
job = client.jobs.get("6958cfd211e2763c3491ef8b")

# Market insights for a cohort (same filter shape as search)
insights = client.jobs.insights({"job_titles": ["Data Scientist"]})
print(insights.headline.median_salary, insights.salary.p90)
```

### Typed inputs

You can pass a plain `dict` or build a typed query:

```python
from hirebase import JobQuery, SalaryRange

query = JobQuery(
    job_titles=["Backend Engineer"],
    salary=SalaryRange(min=150_000, currency="USD"),
    location_types=["Remote"],
    visa=True,
)
result = client.jobs.search(query)
```

## Exporting jobs (async task flow)

Exports are processed server-side and returned as a downloadable file.

```python
query = {
    "job_titles": ["Software Engineer", "Product Engineer", "Fullstack Engineer"],
    "locations": [{"city": "San Francisco", "region": "California",
                   "country": "United States"}],
}

# 1. Start the export -> returns a Task
task = client.jobs.export(query, format="json")   # or format="csv"

# 2. Poll until it finishes -> (success, result)
success, result = client.tasks.poll(task)
if not success:
    raise RuntimeError(f"Export failed: {result.error}")

# 3. Download the file (streamed to disk)
client.stream_file(result["download_url"], file_path="./jobs.json")

# 4. Stream jobs from the file (typed by default; uses constant memory)
for job in client.jobs.stream_file("./jobs.json"):
    print(job.job_title)

# ...or get raw dicts
for row in client.jobs.stream_file("./jobs.json", return_type=dict):
    ...
```

`poll()` accepts a `Task`, a task dict, or a task id, plus `interval`,
`timeout`, and an `on_progress` callback. The result dict contains
`download_url`, `file_size`, `record_count`, and `expiry_time`.

You can also stream **directly from the export URL** without saving to disk
(JSON Lines exports only):

```python
for job in client.jobs.stream_url(result["download_url"]):
    print(job.job_title)
```

## Companies

```python
# Search
companies = client.companies.search({"company_name": "Stripe"})
for company in companies:
    print(company.company_name, company.company_slug)

# Get a company by slug — optionally with its jobs and live insights
company = client.companies.get("stripe", return_jobs=True, return_insights=True)
print(company.description_summary)
print(company.insights_data.headline.total_count)

# Bound helpers (the object remembers its client)
insights = company.insights()
jobs = company.get_jobs(limit=10)

# Company-scoped insights directly
insights = client.companies.insights("stripe", query={"days_ago": 30})
```

## Typed vs. dict responses

Every method returns typed models by default. Pass `return_type=dict` to get
the raw API payload instead:

```python
data = client.jobs.search(query, return_type=dict)   # -> dict
job  = client.jobs.get(job_id, return_type=dict)      # -> dict
```

## Errors

All errors subclass `hirebase.HirebaseError`:

| Exception | Meaning |
|---|---|
| `ConfigurationError` | No API key / bad config |
| `AuthenticationError` | 401 — invalid API key |
| `PaymentRequiredError` | 402 — plan/credits required |
| `PermissionError_` | 403 — not allowed |
| `NotFoundError` | 404 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |
| `APIError` | any other non-2xx (`.status_code`, `.message`, `.body`) |
| `TaskFailed` / `TaskTimeout` | export task failed or timed out |

```python
import hirebase

try:
    client.jobs.search(query)
except hirebase.RateLimitError:
    ...
except hirebase.APIError as e:
    print(e.status_code, e.message)
```

## Development

```bash
pip install -e ".[dev]"

# Offline unit tests (no network)
pytest

# Live integration tests against the real API
HIREBASE_API_KEY=sk_live_... pytest tests/test_integration.py -v
```

> If your environment preloads conflicting pytest plugins, run with
> `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest`.

## License

MIT — see [LICENSE](LICENSE).
