# Errors

Every error raised by the SDK subclasses `hirebase.HirebaseError`, so a single
`except` can catch anything from the library.

```python
import hirebase

try:
    client.jobs.search(query)
except hirebase.HirebaseError as e:
    print("Hirebase call failed:", e)
```

## Exception hierarchy

```
HirebaseError
├── ConfigurationError        # no/invalid client config (e.g. missing API key)
├── APIError                  # any non-2xx HTTP response
│   ├── AuthenticationError   # 401 — missing/invalid API key
│   ├── PaymentRequiredError  # 402 — plan or credits required
│   ├── PermissionError_      # 403 — key valid but not allowed
│   ├── NotFoundError         # 404
│   ├── RateLimitError        # 429
│   └── ServerError           # 5xx
└── TaskError
    ├── TaskFailed            # task ended failed/canceled
    └── TaskTimeout           # task didn't finish within poll timeout
```

## `APIError` attributes

`APIError` (and its subclasses) carry the HTTP context:

```python
try:
    client.jobs.get("does-not-exist")
except hirebase.APIError as e:
    print(e.status_code)   # e.g. 404
    print(e.message)       # human-readable detail from the API
    print(e.body)          # decoded response body (dict or str), if any
```

FastAPI validation errors (422) are flattened into a readable message, e.g.
`body.limit: Limit cannot be greater than 100`.

## Handling specific cases

```python
import time
import hirebase

def search_with_retry(client, query, retries=3):
    for attempt in range(retries):
        try:
            return client.jobs.search(query)
        except hirebase.RateLimitError:
            time.sleep(2 ** attempt)        # back off and retry
        except hirebase.AuthenticationError:
            raise                            # bad key — don't retry
    raise RuntimeError("exhausted retries")
```

## Task errors

`tasks.poll` returns `(False, task)` for a failed/canceled task rather than
raising, so you can inspect `task.error`. It **does** raise `TaskTimeout` if the
task doesn't finish within `timeout`:

```python
try:
    success, result = client.tasks.poll(task, timeout=120)
except hirebase.TaskTimeout as e:
    print("Still running:", e.task.state, e.task.progress)
```

## Configuration errors

Raised before any network call when the client can't be built:

```python
try:
    client = hirebase.Client()      # no api_key arg and no HIREBASE_API_KEY env
except hirebase.ConfigurationError as e:
    print(e)
```

## See also

- [Tasks](./tasks.md) — `TaskTimeout` and polling semantics
- [Getting started](./README.md) — configuration and auth
