"""ResumeRecord id alias behavior."""

from hirebase.models.resumes import ResumeRecord


def test_resume_record_id_from_mongo_underscore_id():
    record = ResumeRecord.model_validate(
        {"_id": "6a2120223c13044930471793", "status": "uploaded"}
    )
    assert record.id == "6a2120223c13044930471793"


def test_resume_record_id_prefers_underscore_id_over_null_id():
    """Parse payloads may carry both keys; ``_id`` must win over ``id: null``."""
    record = ResumeRecord.model_validate(
        {
            "_id": "6a2120223c13044930471793",
            "id": None,
            "status": "parsed",
        }
    )
    assert record.id == "6a2120223c13044930471793"


def test_resume_record_id_from_plain_id():
    record = ResumeRecord.model_validate({"id": "abc", "status": "parsed"})
    assert record.id == "abc"
