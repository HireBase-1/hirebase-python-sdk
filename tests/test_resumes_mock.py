"""Resume upload/embed request wiring (mocked transport)."""

from io import BytesIO

from hirebase.models.resumes import ResumeEmbedResponse, ResumeRecord


def test_resume_embed_multipart(mock_sync_client):
    c = mock_sync_client
    c.transport.add(
        "POST",
        "/v2/resumes/embed",
        {
            "resume": {"personal_information": {"data": {"full_name": "Jane"}}},
            "result": {
                "embedding": [0.1] * 768,
                "dtype": "resume",
                "dim": 768,
                "model_name": "socrates",
                "model_version": "v2",
            },
        },
    )
    out = c.resumes.embed(BytesIO(b"%PDF-1.4 fake"), return_type=None)
    assert isinstance(out, ResumeEmbedResponse)
    assert len(out.embedding) == 768
    req = c.transport.calls[0]
    assert req.files is not None
    assert "file" in req.files


def test_resume_upload_uses_multipart_not_json_session_header(monkeypatch):
    """Regression: session Content-Type: application/json broke file uploads."""
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)

        class Resp:
            status_code = 200
            content = b'{"_id": "r1", "status": "uploaded"}'

        return Resp()

    import hirebase

    client = hirebase.Client(api_key="test-key", base_url="https://api.test")
    monkeypatch.setattr(client._session, "request", fake_request)
    client.resumes.upload(b"%PDF-1.4 fake")

    assert "files" in captured
    assert "file" in captured["files"]
    assert captured.get("json") is None
    assert "Content-Type" not in (captured.get("headers") or {})
    assert "content-type" not in {
        k.lower() for k in (captured.get("headers") or {})
    }
    assert "application/json" not in client._session.headers.get("Content-Type", "")


def test_upload_and_parse_upload_parse_then_get(mock_sync_client):
    c = mock_sync_client
    c.transport.add("POST", "/v2/resumes/upload/", {"_id": "r1", "status": "uploaded"})
    c.transport.add("POST", "/v2/resumes/r1/parse", {"id": None, "status": "parsed"})
    c.transport.add(
        "GET",
        "/v2/resumes/r1",
        {
            "_id": "r1",
            "status": "parsed",
            "parsed_data": {"skills": []},
        },
    )
    out = c.resumes.upload_and_parse(b"resume bytes")
    assert isinstance(out, ResumeRecord)
    assert out.id == "r1"
    assert out.status == "parsed"
    assert c.transport.calls[0].method == "POST"
    assert c.transport.calls[1].path == "/v2/resumes/r1/parse"
    assert c.transport.calls[2].method == "GET"
    assert c.transport.calls[2].path == "/v2/resumes/r1"
