# Hirebase Python SDK — Documentation

A lean, typed Python client for the [Hirebase API](https://docs.hirebase.org/).

## Contents

- [Getting started](#getting-started) (this page)
- [Jobs](./jobs.md) — search, fetch, insights, exports, and streaming
- [Companies](./companies.md) — search, fetch, company jobs, and insights
- [Tasks](./tasks.md) — polling async work (e.g. exports) to completion
- [Resumes](./resumes.md) — upload/parse (public) and enterprise embed (vectors)
- [Errors](./errors.md) — the exception hierarchy and how to handle failures

## Installation

```bash
pip install hirebase

# Optional extras
pip install "hirebase[streaming]"   # ijson, for streaming JSON-array exports
pip install "hirebase[cli]"         # the bundled `hirebase` command-line tool
```

Requires Python 3.9+.

## Authentication

Pass your API key directly, or via the environment. Resolution order for every
setting is **argument → environment variable → default**.

```python
import hirebase

client = hirebase.Client(api_key="sk_live_...")
```

```bash
export HIREBASE_API_KEY="sk_live_..."
export HIREBASE_BASE_URL="https://api.hirebase.org"   # optional; this is the default
```

| Setting    | Argument    | Environment variable                      | Default                     |
|------------|-------------|-------------------------------------------|-----------------------------|
| API key    | `api_key`   | `HIREBASE_API_KEY`                        | — (required)                |
| Base URL   | `base_url`  | `HIREBASE_BASE_URL` / `HIREBASE_API_URL`  | `https://api.hirebase.org`  |
| Timeout    | `timeout`   | —                                         | `30.0` seconds              |

The key is sent on every request as the `X-API-Key` header.

## Sync vs. async

Two clients with identical method signatures. The async methods are awaitable.

```python
import hirebase

# Synchronous (requests under the hood)
client = hirebase.Client(api_key="sk_live_...")
result = client.jobs.search({"job_titles": ["Software Engineer"]})

# Context-managed (closes the HTTP session on exit)
with hirebase.Client() as client:
    result = client.jobs.search({"job_titles": ["Software Engineer"]})
```

```python
import asyncio, hirebase

async def main():
    async with hirebase.AsyncClient() as client:   # httpx under the hood
        result = await client.jobs.search({"job_titles": ["Software Engineer"]})
        for job in result:
            print(job.job_title)

asyncio.run(main())
```

## Typed by default (and dicts when you want them)

Every method returns Pydantic models by default. Pass `return_type=dict` on any
call to get the raw API payload instead.

```python
typed = client.jobs.search(query)                 # -> JobSearchResult (iterable)
raw   = client.jobs.search(query, return_type=dict)  # -> dict
```

Result containers (`JobSearchResult`, `CompanySearchResult`) are iterable and
indexable:

```python
result = client.jobs.search(query)
print(result.total_count, "matches across", result.total_pages, "pages")
first = result[0]
for job in result:
    ...
```

## A complete example

Search, then run an export end-to-end:

```python
import hirebase

client = hirebase.Client(api_key="sk_live_...")

query = {
    "job_titles": ["Software Engineer", "Product Engineer"],
    "locations": [{"city": "San Francisco", "region": "California",
                   "country": "United States"}],
    "limit": 50,
}

# Live search
result = client.jobs.search(query)
for job in result:
    print(job.job_title, "@", job.company_name)

# Bulk export (async task -> download -> stream)
task = client.jobs.export(query, format="json")
success, export = client.tasks.poll(task)
if success:
    client.stream_file(export["download_url"], file_path="./jobs.json")
    for job in client.jobs.stream_file("./jobs.json"):
        ...
```

Next: dive into [Jobs](./jobs.md), [Companies](./companies.md), or
[Tasks](./tasks.md).
