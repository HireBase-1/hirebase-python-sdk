"""Neural search request building and job-id resolution."""

import hirebase
from hirebase import _ops as ops
from hirebase.models.jobs import Job
from hirebase.models.neural import (
    NeuralVectorQuery,
    coerce_neural_vector,
    extract_job_id,
    merge_job_ids,
)


def test_neural_vector_payload():
    v = coerce_neural_vector(
        {"query": "ml engineer", "resume_id": "abc123", "score_threshold": 0.5}
    )
    payload = v.to_payload()
    assert payload["query"] == "ml engineer"
    assert payload["artifact_id"] == "abc123"
    assert payload["score_threshold"] == 0.5


def test_neural_vector_validates_dim():
    import pytest

    v = NeuralVectorQuery(vectors=[[0.0] * 768])
    assert len(v.to_payload()["vectors"][0]) == 768
    with pytest.raises(ValueError):
        NeuralVectorQuery(vectors=[[1.0, 2.0]]).to_payload()


def test_extract_job_id_from_job_model():
    job = Job.model_validate({"_id": "jid1", "job_title": "SWE"})
    assert extract_job_id(job) == "jid1"


def test_merge_job_ids_dedupes():
    v = merge_job_ids(
        NeuralVectorQuery(job_ids=["a"]),
        job_ids=["a", "b"],
        job="c",
    )
    assert v.job_ids == ["a", "b", "c"]


def test_neural_search_request_shape():
    search = hirebase.NeuralSearchQuery(
        vector=NeuralVectorQuery(query="backend"),
        lexical=hirebase.JobQuery(location_types=["Remote"], limit=5),
    )
    req = ops.neural_search_request(search, page=2)
    body = req.json
    assert req.path == "/v2/jobs/neural-search"
    assert body["vector"]["query"] == "backend"
    assert body["lexical"]["location_types"] == ["Remote"]
    assert body["lexical"]["page"] == 2
    assert body["lexical"]["limit"] == 5


def test_neural_search_resolves_slug(mock_sync_client):
    c = mock_sync_client
    c.transport.add(
        "GET",
        "/v2/hirebase/companies/stripe/jobs/swe-role",
        {"jobs": [{"_id": "job-from-slug", "job_title": "SWE"}]},
    )
    c.transport.add(
        "POST",
        "/v2/jobs/neural-search",
        {
            "jobs": [{"_id": "1", "job_title": "Match", "vector_score": 0.9}],
            "total_count": 1,
            "company_count": 1,
            "page": 1,
            "limit": 10,
            "total_pages": 1,
        },
    )
    result = c.jobs.neural_search(
        text="similar roles",
        company_slug="stripe",
        job_slug="swe-role",
        lexical={"limit": 10},
    )
    assert result.jobs[0].vector_score == 0.9
    neural_req = c.transport.calls[-1]
    assert "job-from-slug" in neural_req.json["vector"]["job_ids"]
