#!/usr/bin/env python3
"""Enterprise / ML: embed resume privately (vectors only), search without storing PII."""

from _common import (
    banner,
    fetch_sample_resume,
    marker,
    print_job_row,
    require_api_key,
    step,
)

import hirebase
from hirebase.exceptions import APIError


def main() -> None:
    require_api_key()
    banner(
        "Enterprise — private embed + vector search",
        "ML engineers & enterprise API customers",
        "Resume is parsed and embedded in one call; nothing persisted server-side.",
    )

    client = hirebase.Client()
    pdf_bytes = fetch_sample_resume()

    step(1, "POST /v2/resumes/embed (enterprise)")
    marker("REQUEST", "Returns parsed resume + 768-d vector — NOT stored on Hirebase")
    try:
        embed = client.resumes.embed(pdf_bytes)
    except APIError as e:
        marker(
            "PERMISSION",
            f"{e.message} — this endpoint needs commercial embed access on your API key.",
        )
        client.close()
        return

    print(f"    Embedding dim: {embed.result.dim}")
    print(f"    Model:         {embed.result.model_name} {embed.result.model_version}")
    pi = embed.resume.get("personal_information", {})
    if isinstance(pi, dict):
        data = (pi.get("data") or {}) if isinstance(pi.get("data"), dict) else pi
        if isinstance(data, dict) and data.get("full_name"):
            print(f"    Parsed name:   {data.get('full_name')} (only in your process — not stored)")

    step(2, "Neural search with explicit vectors (no resume_id needed)")
    marker("REQUEST", "POST /v2/jobs/neural-search with vectors=[embedding]")
    matches = client.jobs.neural_search(
        vectors=[embed.embedding],
        lexical={
            "job_titles": ["Software Engineer", "Research Engineer"],
            "location_types": ["Remote"],
            "limit": 6,
        },
    )
    marker("RESULT", "Semantic match driven by your local vector")
    for job in matches:
        print_job_row(job, show_score=True)

    step(3, "Optional: also pass a text query alongside the vector")
    marker("REQUEST", "vector.query + vectors can be combined")
    blended = client.jobs.neural_search(
        text="computer vision and deep learning research",
        vectors=[embed.embedding],
        lexical={"limit": 4},
    )
    for job in blended:
        print_job_row(job, show_score=True)

    marker("DONE", "Keep vectors in your vault; never send resume files again after embed.")
    client.close()


if __name__ == "__main__":
    main()
