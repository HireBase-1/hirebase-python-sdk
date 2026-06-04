# Tasks

Some operations run asynchronously on the server and return a **Task** you poll
to completion. The most common is a job [export](./jobs.md#exporting-jobs).

The `client.tasks` resource fetches and polls these tasks.

```python
import hirebase
client = hirebase.Client(api_key="sk_live_...")
```

---

## The `Task` model

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Task identifier |
| `type` | `str` | e.g. `"export_job_data"` |
| `state` | `TaskState` | `queued`, `processing`, `finished`, `failed`, `canceled` |
| `progress` | `float` | `0.0`–`1.0` |
| `result` | `dict \| None` | Present on success |
| `error` | `str \| None` | Present on failure |
| `created_at` / `updated_at` / `completed_at` | `datetime` | Timestamps |

Convenience properties:

```python
task.is_done        # True if state is finished/failed/canceled
task.succeeded      # True only if state == finished
task.download_url   # shortcut for result["download_url"] (exports)
```

For an export, `task.result` is a dict with:
`download_url`, `file_size`, `record_count`, `expiry_time`.

---

## `tasks.get(task_id, *, return_type=None)`

Fetch the current state of a task by id. Returns a `Task`.

```python
task = client.tasks.get("a1b2c3d4")
print(task.state, task.progress)
```

---

## `tasks.poll(task, *, interval=2.0, timeout=300.0, on_progress=None)`

Poll a task until it reaches a terminal state. Returns a tuple
**`(success, result)`**:

- on success → `(True, result_dict)` — the task's `result` (e.g. with
  `download_url`)
- on failure/cancel → `(False, task)` — the failed `Task` (inspect `.error`)

`task` may be a `Task`, a task dict, or a task id string.

```python
task = client.jobs.export(query, format="json")

success, result = client.tasks.poll(task)
if success:
    print("Download:", result["download_url"])
    client.stream_file(result["download_url"], file_path="./jobs.json")
else:
    print("Export failed:", result.error)
```

### Options

| Argument | Default | Meaning |
|---|---|---|
| `interval` | `2.0` | Seconds between polls |
| `timeout` | `300.0` | Max seconds to wait; `None` waits forever |
| `on_progress` | `None` | Callback invoked with the latest `Task` each poll |

```python
def show(task):
    print(f"{task.state.value}: {task.progress:.0%}")

success, result = client.tasks.poll(task, interval=3, timeout=600, on_progress=show)
```

If `timeout` elapses before the task finishes, `poll` raises
`hirebase.TaskTimeout` (the last-seen `Task` is on the exception's `.task`).

### Bound helper

A `Task` returned by the client can poll itself:

```python
task = client.jobs.export(query)
success, result = task.poll(interval=3)
```

---

## Async

Identical API; `await` the calls. Polling sleeps with `asyncio.sleep`, so it
never blocks the event loop.

```python
import hirebase

async def export(query):
    async with hirebase.AsyncClient() as client:
        task = await client.jobs.export(query, format="json")
        success, result = await client.tasks.poll(task, interval=3)
        if success:
            await client.stream_file(result["download_url"], file_path="jobs.json")
            async for job in client.jobs.stream_url(result["download_url"]):
                ...
```

---

## See also

- [Jobs](./jobs.md) — see "Exporting jobs" for creating the export task
- [Errors](./errors.md) — `TaskTimeout` and the wider exception hierarchy
