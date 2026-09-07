#!/usr/bin/env python3
"""Compensation / HR: queue a posted-salary benchmark with AsyncClient."""

import asyncio

from _common import banner, marker, require_api_key, step

import hirebase
from hirebase import SalaryBenchmarkRequest


async def main() -> None:
    require_api_key()
    banner(
        "Salary benchmark",
        "Compensation, HR, recruiting ops",
        "await jobs.salary_benchmark → poll GET /v2/tasks/{id} → read the report.",
    )

    request = SalaryBenchmarkRequest(
        job_title="Senior Software Engineer",
        yoe_range={"min": 5, "max": 10},
        geo_locations=[{"country": "United States"}],
        days_ago=90,
    )

    async with hirebase.AsyncClient() as client:
        step(1, "await client.jobs.salary_benchmark(...)")
        marker("REQUEST", request.job_title or "")
        task = await client.jobs.salary_benchmark(request)
        print(f"    Task id: {task.id} | type={task.type} | state={task.state.value}")

        step(2, "await client.tasks.poll(task)")

        def on_progress(current) -> None:
            print(f"    … state={current.state.value} progress={current.progress:.0%}")

        success, report = await client.tasks.poll(
            task, interval=5, timeout=900, on_progress=on_progress
        )
        if not success:
            marker("FAILED", getattr(report, "error", report))
            return

        step(3, "Read market percentiles from the finished task")
        market = (report or {}).get("market") or {}
        salary = market.get("salary") or {}
        conf = (report or {}).get("confidence") or {}
        print(
            f"    n={salary.get('count')} | median {salary.get('p50')} | "
            f"confidence {conf.get('grade') or '—'}"
        )
        proposed = (report or {}).get("proposed")
        if proposed and proposed.get("percentile") is not None:
            print(
                f"    proposed {proposed.get('min')}–{proposed.get('max')} "
                f"sits at p{proposed['percentile']}"
            )

    marker("DONE", "Same method exists on hirebase.Client without await.")


if __name__ == "__main__":
    asyncio.run(main())
