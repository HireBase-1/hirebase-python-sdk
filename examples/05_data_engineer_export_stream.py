#!/usr/bin/env python3
"""Data engineers: bulk export jobs to JSONL and stream without loading into memory."""

import tempfile
from pathlib import Path

from _common import banner, marker, print_job_row, require_api_key, step

import hirebase


def main() -> None:
    require_api_key()
    banner(
        "Data engineer — export & stream",
        "Data engineers & analytics pipelines",
        "Async export task → poll → download → stream JSON Lines locally.",
    )

    client = hirebase.Client()

    # Keep limit small while testing — exports are metered by job count.
    query = {
        "job_titles": ["Software Engineer"],
        "location_types": ["Remote"],
        "days_ago": 14,
        "limit": 25,
    }

    step(1, "POST /v2/jobs/export → creates background Task")
    marker("REQUEST", "format=json, search filters in body")
    task = client.jobs.export(query, format="json")
    print(f"    Task id: {task.id} | state: {task.state.value}")

    step(2, "Poll task until finished")
    marker("POLL", "GET /v2/tasks/{id} every few seconds")

    def on_progress(t):
        print(f"    … state={t.state.value} progress={t.progress:.0%}")

    success, result = client.tasks.poll(task, interval=2, timeout=300, on_progress=on_progress)

    if not success:
        marker("FAILED", getattr(result, "error", result))
        client.close()
        return

    url = result["download_url"]
    marker("SUCCESS", f"download_url ready | records≈{result.get('record_count', '?')}")

    step(3, "Stream download to disk (no full-file buffer in SDK)")
    out_dir = Path(tempfile.mkdtemp(prefix="hirebase-export-"))
    out_path = out_dir / "jobs.json"
    marker("DOWNLOAD", str(out_path))
    client.stream_file(url, file_path=str(out_path))
    print(f"    File size: {out_path.stat().st_size:,} bytes")

    step(4, "Stream-parse jobs (constant memory)")
    marker("STREAM", "ijson-friendly JSON Lines, one job per line")
    count = 0
    for job in client.jobs.stream_file(str(out_path)):
        count += 1
        if count <= 3:
            print_job_row(job)
    print(f"    … streamed {count} jobs total")

    marker("DONE", f"Point your ETL at {out_path} or stream in-process.")
    client.close()


if __name__ == "__main__":
    main()
