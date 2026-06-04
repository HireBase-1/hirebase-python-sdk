"""Live integration tests against the real Hirebase API.

These are skipped unless ``HIREBASE_API_KEY`` is set. Point at a non-prod
deployment with ``HIREBASE_BASE_URL`` if desired. They make real, metered
requests, so keep them light.

Run with:
    HIREBASE_API_KEY=sk_live_... pytest tests/test_integration.py -v
"""

import os

import pytest

import hirebase
from hirebase.models.companies import CompanySearchResult
from hirebase.models.jobs import JobSearchResult

pytestmark = pytest.mark.skipif(
    not os.getenv("HIREBASE_API_KEY"),
    reason="HIREBASE_API_KEY not set; skipping live integration tests.",
)


@pytest.fixture
def client():
    c = hirebase.Client()
    yield c
    c.close()


def test_live_jobs_search(client):
    res = client.jobs.search(
        {"job_titles": ["Software Engineer"], "limit": 3}
    )
    assert isinstance(res, JobSearchResult)
    assert res.limit == 3
    for job in res:
        assert job.job_title is not None


def test_live_jobs_search_dict(client):
    res = client.jobs.search({"job_titles": ["Software Engineer"], "limit": 1}, return_type=dict)
    assert isinstance(res, dict)
    assert "jobs" in res


def test_live_companies_search(client):
    res = client.companies.search({"company_name": "Stripe", "limit": 3})
    assert isinstance(res, CompanySearchResult)
    assert len(res.companies) >= 0


def test_live_company_get(client):
    # Resolve a real slug first to avoid hardcoding.
    res = client.companies.search({"company_name": "Stripe", "limit": 1})
    if not res.companies:
        pytest.skip("No company found to fetch.")
    slug = res.companies[0].company_slug
    company = client.companies.get(slug)
    assert company.company_slug == slug


def test_live_export_roundtrip(tmp_path, client):
    """Full export -> poll -> download -> stream flow."""
    task = client.jobs.export(
        {"job_titles": ["Software Engineer"], "limit": 5}, format="json"
    )
    success, result = client.tasks.poll(task, interval=3, timeout=300)
    assert success, f"Export failed: {result}"
    url = result["download_url"]
    out = tmp_path / "jobs.json"
    client.stream_file(url, file_path=str(out))
    assert out.exists()
    jobs = list(client.jobs.stream_file(str(out)))
    assert len(jobs) >= 1
