"""Local file streaming (JSONL + CSV)."""

import json

from hirebase.models.jobs import Job
from hirebase.streaming import stream_jobs_file


def test_stream_jsonl_typed(tmp_path):
    p = tmp_path / "jobs.json"
    p.write_text(
        json.dumps({"_id": "1", "job_title": "SWE"}) + "\n"
        + "\n"  # blank line ignored
        + json.dumps({"_id": "2", "job_title": "PM"}) + "\n"
    )
    jobs = list(stream_jobs_file(str(p)))
    assert all(isinstance(j, Job) for j in jobs)
    assert [j.id for j in jobs] == ["1", "2"]


def test_stream_jsonl_dict(tmp_path):
    p = tmp_path / "jobs.json"
    p.write_text(json.dumps({"_id": "1", "job_title": "SWE"}) + "\n")
    rows = list(stream_jobs_file(str(p), return_type=dict))
    assert rows[0]["job_title"] == "SWE"
    assert isinstance(rows[0], dict)


def test_stream_csv_decodes_json_cells(tmp_path):
    p = tmp_path / "jobs.csv"
    p.write_text('_id,job_title,skills\n5,Engineer,"[""python"", ""go""]"\n')
    jobs = list(stream_jobs_file(str(p)))
    assert jobs[0].job_title == "Engineer"
    assert jobs[0].skills == ["python", "go"]


def test_format_override(tmp_path):
    # File without a .csv extension still parsed as CSV when forced.
    p = tmp_path / "data.txt"
    p.write_text("_id,job_title\n1,SWE\n")
    jobs = list(stream_jobs_file(str(p), fmt="csv"))
    assert jobs[0].job_title == "SWE"
