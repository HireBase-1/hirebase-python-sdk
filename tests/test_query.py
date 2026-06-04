"""Query serialization: aliases, bool->'true', extra fields, export shape."""

from hirebase import _ops as ops
from hirebase.models.companies import CompanyQuery, coerce_company_query
from hirebase.models.jobs import JobQuery, coerce_query


def test_locations_alias_maps_to_geo_locations():
    q = coerce_query({"locations": [{"city": "SF", "country": "United States"}]})
    payload = q.to_payload()
    assert "geo_locations" in payload
    assert payload["geo_locations"][0]["city"] == "SF"
    assert "locations" not in payload


def test_bool_fields_convert_to_string_true_and_drop_false():
    q = JobQuery(visa=True, include_no_salary=False, include_expired=True)
    payload = q.to_payload()
    assert payload["visa"] == "true"
    assert payload["include_expired"] == "true"
    assert "include_no_salary" not in payload  # False is dropped


def test_company_name_alias_and_extra_fields_preserved():
    q = coerce_query({"company_name": "Stripe", "some_new_field": 1})
    payload = q.to_payload()
    assert payload["company_names"] == "Stripe"
    assert payload["some_new_field"] == 1


def test_none_values_excluded():
    payload = JobQuery(job_titles=["Eng"]).to_payload()
    assert payload == {"job_titles": ["Eng"]}


def test_search_request_overrides_page_and_limit():
    req = ops.search_jobs_request({"job_titles": ["Eng"]}, page=3, limit=25)
    assert req.method == "POST"
    assert req.path == "/v2/jobs/search"
    assert req.json["page"] == 3
    assert req.json["limit"] == 25


def test_export_request_shape_and_format_validation():
    req = ops.export_jobs_request({"job_titles": ["Eng"]}, format="csv")
    assert req.path == "/v2/jobs/export"
    assert req.json["format"] == "csv"
    assert req.json["search"]["job_titles"] == ["Eng"]


def test_export_invalid_format_raises():
    import pytest

    with pytest.raises(ValueError):
        ops.export_jobs_request({}, format="xml")


def test_company_query_payload():
    q = coerce_company_query({"company_name": "Stripe", "industries": ["Tech"]})
    payload = q.to_payload()
    assert payload["company_name"] == "Stripe"
    assert payload["industries"] == ["Tech"]


def test_typed_query_objects_passthrough():
    q = JobQuery(job_titles=["Eng"], limit=5)
    assert coerce_query(q) is q
