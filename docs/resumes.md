# Resumes

The `client.resumes` resource covers two flows:

| Flow | Method | Storage | Returns |
|------|--------|---------|---------|
| **Public** | `upload` → `parse` / `upload_and_parse` | Resume file stored on Hirebase | Parsed resume + resume id for search |
| **Enterprise** | `embed` | **Not stored** (data stays private) | Parsed fields + 768-d embedding vector |

Enterprise embed requires an API key with commercial embed permission.
See the [Embed Resume API reference](https://www.hirebase.org/docs/api-reference/resumes/embed-post).

---

## Public flow (stored resume)

Upload a PDF/Word/text/HTML file (max 5 MB), then parse it. The SDK can do both steps for you.

```python
import hirebase

client = hirebase.Client(api_key="sk_live_...")

# One step: upload + parse (finishes with GET for a canonical record)
resume = client.resumes.upload_and_parse("./resume.pdf")
print(resume.id, resume.parsed_data)

# Or explicitly:
uploaded = client.resumes.upload("./resume.pdf")
client.resumes.parse(uploaded.id)
resume = client.resumes.get(uploaded.id)
```

Use the resume id with neural search:

```python
matches = client.jobs.neural_search(
    resume_id=parsed.id,   # same as artifact_id
    lexical={"location_types": ["Remote"], "limit": 20},
)
```

---

## Enterprise flow (private embed)

Parse and embed in a single request. Nothing is persisted server-side; you receive the vector to use in your own systems.

```python
result = client.resumes.embed("./resume.pdf")

print(result.resume)          # parsed structured data (dict-like model)
vector = result.embedding     # 768 floats — use in neural search

matches = client.jobs.neural_search(
    vectors=[vector],
    lexical={"job_titles": ["Software Engineer"], "limit": 25},
)
```

`ResumeEmbedResponse` fields:

- `resume` — parsed content (personal info, skills, experience, …)
- `result` — `EmbeddingResult` with `embedding`, `dim`, `model_name`, …

---

## File inputs

All methods accept:

- A filesystem path (`str` or `pathlib.Path`)
- Raw `bytes`
- A file-like object (`open(..., "rb")`, `BytesIO`, …)
- A tuple `(filename, data)` or `(filename, data, content_type)`

---

## Async

```python
async with hirebase.AsyncClient() as client:
    resume = await client.resumes.upload_and_parse("./resume.pdf")
    embed = await client.resumes.embed("./resume.pdf")
```

---

## See also

- [Jobs → neural search](./jobs.md#jobsneural_search) — hybrid search using vectors, queries, resume ids, and job references
- [Getting started](./README.md)
