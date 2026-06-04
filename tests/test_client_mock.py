"""End-to-end resource behavior against a stubbed transport (no network)."""

import asyncio

import pytest

import hirebase
from hirebase.exceptions import (
    AuthenticationError,
    NotFoundError,
    TaskTimeout,
    error_from_response,
)
from hirebase.models.companies import Company
from hirebase.models.jobs import JobSearchResult
from hirebase.models.tasks import Task


def test_jobs_search_sync(mock_sync_client):
    c = mock_sync_client
    c.transport.add(
        "POST",
        "/v2/jobs/search",
        {"jobs": [{"_id": "1", "job_title": "SWE"}], "total_count": 1, "company_count": 1, "page": 1, "limit": 10, "total_pages": 1},
    )
    res = c.jobs.search({"job_titles": ["SWE"]})
    assert isinstance(res, JobSearchResult)
    assert res.jobs[0].job_title == "SWE"
    # The job should be bound to the client.
    assert res.jobs[0]._client is c


def test_jobs_export_returns_task(mock_sync_client):
    c = mock_sync_client
    c.transport.add("POST", "/v2/jobs/export", {"id": "task-1", "state": "queued"})
    task = c.jobs.export({"job_titles": ["SWE"]}, format="json")
    assert isinstance(task, Task)
    assert task.id == "task-1"
    assert task._client is c


def test_tasks_poll_success(mock_sync_client):
    c = mock_sync_client
    states = iter(["processing", "finished"])

    def respond(req):
        state = next(states)
        result = {"download_url": "http://x/y.json"} if state == "finished" else None
        return {"id": "task-1", "state": state, "result": result}

    c.transport.add("GET", "/v2/tasks/task-1", respond)
    success, result = c.tasks.poll("task-1", interval=0)
    assert success is True
    assert result == {"download_url": "http://x/y.json"}


def test_tasks_poll_failure_returns_task(mock_sync_client):
    c = mock_sync_client
    c.transport.add("GET", "/v2/tasks/t2", {"id": "t2", "state": "failed", "error": "boom"})
    success, result = c.tasks.poll("t2", interval=0)
    assert success is False
    assert isinstance(result, Task)
    assert result.error == "boom"


def test_tasks_poll_timeout(mock_sync_client):
    c = mock_sync_client
    c.transport.add("GET", "/v2/tasks/t3", {"id": "t3", "state": "processing"})
    with pytest.raises(TaskTimeout):
        c.tasks.poll("t3", interval=0, timeout=0.01)


def test_company_get_with_insights(mock_sync_client):
    c = mock_sync_client
    c.transport.add(
        "GET",
        "/v2/hirebase/companies/stripe",
        {"company": {"company_slug": "stripe", "company_name": "Stripe"}, "jobs": []},
    )
    c.transport.add(
        "POST",
        "/v2/hirebase/companies/stripe/insights",
        {"headline": {"total_count": 7}, "salary": {"count": 7}},
    )
    company = c.companies.get("stripe", return_insights=True)
    assert isinstance(company, Company)
    assert company.company_slug == "stripe"
    assert company.insights_data.headline.total_count == 7
    # Bound helper should reach the same endpoint.
    again = company.insights()
    assert again.headline.total_count == 7


def test_company_bound_get_jobs(mock_sync_client):
    c = mock_sync_client
    c.transport.add(
        "GET",
        "/v2/hirebase/companies/stripe",
        {"company": {"company_slug": "stripe", "company_name": "Stripe"}, "jobs": []},
    )
    c.transport.add(
        "GET",
        "/v2/hirebase/companies/stripe/jobs",
        {"jobs": [{"_id": "j1", "job_title": "SWE"}], "job_categories": [], "total_count": 1, "page": 1, "limit": 10, "total_pages": 1},
    )
    company = c.companies.get("stripe")
    jobs = company.get_jobs(limit=5)
    assert jobs[0].job_title == "SWE"


def test_dict_return_type(mock_sync_client):
    c = mock_sync_client
    payload = {"jobs": [], "total_count": 0, "company_count": 0, "page": 1, "limit": 10, "total_pages": 0}
    c.transport.add("POST", "/v2/jobs/search", payload)
    res = c.jobs.search({}, return_type=dict)
    assert res is payload


def test_async_search_and_poll(mock_async_client):
    c = mock_async_client

    async def run():
        c.transport.add(
            "POST",
            "/v2/jobs/search",
            {"jobs": [{"_id": "1", "job_title": "SWE"}], "total_count": 1, "company_count": 1, "page": 1, "limit": 10, "total_pages": 1},
        )
        res = await c.jobs.search({"job_titles": ["SWE"]})
        assert res.jobs[0].job_title == "SWE"

        states = iter(["queued", "finished"])

        def respond(req):
            s = next(states)
            return {"id": "tA", "state": s, "result": {"download_url": "u"} if s == "finished" else None}

        c.transport.add("GET", "/v2/tasks/tA", respond)
        ok, result = await c.tasks.poll("tA", interval=0)
        assert ok and result["download_url"] == "u"
        await c.aclose()

    asyncio.run(run())


def test_error_mapping():
    assert isinstance(error_from_response(401, {"detail": "no"}), AuthenticationError)
    assert isinstance(error_from_response(404, {"detail": "missing"}), NotFoundError)
    err = error_from_response(422, {"detail": [{"loc": ["body", "x"], "msg": "required"}]})
    assert "body.x" in str(err)


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("HIREBASE_API_KEY", raising=False)
    with pytest.raises(hirebase.ConfigurationError):
        hirebase.Client()
