"""Response parsing into typed models."""

from hirebase import _ops as ops
from hirebase.models.companies import Company, CompanySearchResult
from hirebase.models.insights import JobInsights
from hirebase.models.jobs import Job, JobSearchResult
from hirebase.models.tasks import Task, TaskState


def test_parse_job_search_typed_and_iterable():
    data = {
        "jobs": [{"_id": "a", "job_title": "SWE", "company_name": "Stripe"}],
        "total_count": 1,
        "company_count": 1,
        "page": 1,
        "limit": 10,
        "total_pages": 1,
    }
    res = ops.parse_job_search(data, client=None, return_type=None)
    assert isinstance(res, JobSearchResult)
    assert res.jobs[0].id == "a"
    assert len(res) == 1
    assert [j.company_name for j in res] == ["Stripe"]


def test_parse_job_search_dict_passthrough():
    data = {"jobs": [], "total_count": 0, "company_count": 0, "page": 1, "limit": 10, "total_pages": 0}
    res = ops.parse_job_search(data, client=None, return_type=dict)
    assert res is data


def test_parse_job_handles_id_alias():
    job = ops.parse_job({"_id": "xyz", "job_title": "PM"}, client=None, return_type=None)
    assert isinstance(job, Job)
    assert job.id == "xyz"


def test_parse_task_helpers():
    task = ops.parse_task(
        {"id": "t1", "state": "finished", "result": {"download_url": "u"}},
        client=None,
        return_type=None,
    )
    assert isinstance(task, Task)
    assert task.state == TaskState.FINISHED
    assert task.succeeded is True
    assert task.is_done is True
    assert task.download_url == "u"


def test_task_id_of_accepts_str_dict_and_model():
    assert ops.task_id_of("abc") == "abc"
    assert ops.task_id_of({"id": "def"}) == "def"
    task = ops.parse_task({"id": "ghi", "state": "queued"}, client=None, return_type=None)
    assert ops.task_id_of(task) == "ghi"


def test_parse_company_detail_attaches_jobs():
    data = {
        "company": {"company_slug": "stripe", "company_name": "Stripe"},
        "jobs": [{"_id": "1", "job_title": "SWE"}],
    }
    company = ops.parse_company_detail(data, client=None, return_type=None, return_jobs=True)
    assert isinstance(company, Company)
    assert company.company_slug == "stripe"
    assert company.jobs[0].job_title == "SWE"


def test_parse_company_detail_without_jobs():
    data = {"company": {"company_slug": "stripe", "company_name": "Stripe"}, "jobs": [{"_id": "1"}]}
    company = ops.parse_company_detail(data, client=None, return_type=None, return_jobs=False)
    assert company.jobs is None


def test_parse_company_search():
    data = {
        "companies": [{"company_slug": "s", "company_name": "S"}],
        "total_count": 1,
        "page": 1,
        "limit": 10,
        "total_pages": 1,
    }
    res = ops.parse_company_search(data, client=None, return_type=None)
    assert isinstance(res, CompanySearchResult)
    assert res[0].company_name == "S"


def test_parse_insights():
    data = {"headline": {"total_count": 3, "median_salary": 120000}, "salary": {"count": 3, "p50": 120000}}
    ins = ops.parse_insights(data, client=None, return_type=None)
    assert isinstance(ins, JobInsights)
    assert ins.headline.total_count == 3
    assert ins.salary.p50 == 120000


def test_company_jobs_defaults_company_count():
    data = {"jobs": [{"_id": "1"}], "total_count": 1, "page": 1, "limit": 10, "total_pages": 1}
    res = ops.parse_company_jobs(data, client=None, return_type=None)
    assert res.company_count == 0
    assert len(res) == 1
