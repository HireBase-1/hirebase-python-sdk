# Hirebase — Engineering Context

This file has two parts. **Shared Hirebase context** is identical across every Hirebase repo (hirebase-api, data-pulse-hire, hirebase-web, hirebase-python-sdk, hirebase-ats-detector); if you change it, change it everywhere. **This repo** at the bottom is specific to the repo you are in.

## Shared Hirebase context

### How to think

Use good judgment. These are guidelines, not rigid rules.
Optimize for the 80/20: make changes that meaningfully improve the product, reliability, customer experience, or our ability to operate the system.
Prefer simple, high-impact solutions over technically complete or theoretically ideal ones.
Before making a meaningful change, ask:

1. What behavior is actually desired?
2. What is this feature or code path intended to do?
3. Who uses it and how?
4. Is the current behavior actually a problem?
5. Is each change I'm making necessary or meaningfully useful?
6. Is there a simpler way to get most of the benefit?

Do not confuse "this could work differently" with "this needs to be changed."

### Understand product intent

Code should be interpreted in the context of the product.
Before changing a feature, endpoint, or workflow, try to understand:

* why it exists
* its primary use case
* whether it is customer-facing, internal, or experimental
* what behavior users actually rely on
* what it intentionally does not support
* relevant performance, cost, scale, or accuracy tradeoffs

Use the codebase to investigate this when necessary. Look at callers, routes, tests, documentation, frontend usage, comments, schemas, and related implementations.
A limitation or inconsistency is not automatically a bug. Some functionality is intentionally narrow. For example: the expired-jobs feed returns identifiers only and costs nothing; the missing job bodies are deliberate, not a gap to fill. Understand the intended use case before expanding behavior.

### Make the smallest useful change

Generally prefer: small fix → change existing behavior → extend an existing abstraction → create a new abstraction → architectural change.
But use judgment. Do not avoid a larger change when the larger change is clearly worthwhile.
For every meaningful addition, ask: if I didn't make this part of the change, would the user or product meaningfully suffer? If not, consider leaving it out.
Avoid doing work primarily because it makes the system more theoretically complete. Be cautious about:

* unrelated refactors
* abstractions for one-off cases
* speculative future-proofing
* configuration nobody currently needs
* making all endpoints support the same functionality
* defensive handling for extremely unlikely situations
* broad architectural changes when a local solution is sufficient

Do not over-engineer, but do not be afraid to improve architecture when there is a concrete payoff.

### Bugs

If something is clearly a real bug affecting intended behavior, fix it. A small, obvious bug does not need an elaborate product justification. Use proportionality:

* obvious bug + simple fix → fix it
* significant bug → investigate enough to understand the root cause
* behavior that merely looks strange → determine whether it is actually unintended before changing it

Do not expand the scope of a bug fix unnecessarily.

### Prioritize impact

When deciding what work is worth doing, consider customer impact, frequency, severity, reliability, data quality, freshness, performance, infrastructure / inference cost, engineering complexity, and future maintenance burden.
Spend more effort where the expected impact is high. Do not spend substantial engineering effort perfecting low-value edge cases. A solution that captures 90% of the value with 20% of the complexity is often preferable.

### Hirebase-specific principles

Hirebase operates at large data volume, so seemingly small increases in per-job processing, inference, storage, or requests can matter at scale.
For job data:

* Prefer source evidence over unsupported inference.
* Accuracy and trustworthiness matter more than artificially filling every field.
* `null` can be better than a confident hallucination.
* Consider processing and inference cost when adding classification.
* Freshness and reliability are important product characteristics.

Do not add expensive processing unless the expected improvement justifies the cost.

### The Hirebase system

* **hirebase-api** — FastAPI backend at api.hirebase.org. Serves both the web app and API-key customers. `develop` deploys dev, `main` deploys prod.
* **data-pulse-hire** — the web app at app.hirebase.org. Talks to the API with a user JWT.
* **hirebase-web** — the marketing site at www.hirebase.org. The public API docs at www.hirebase.org/docs are Mintlify, published from the `mint` branch of hirebase-api.
* **hirebase-python-sdk** — the public Python client for the API.
* **hirebase-ats-detector** — detects which applicant tracking system a company uses, feeding scraping coverage.
* The job corpus, standard search, semantic (neural/vector) search, and scraping live in the private `jolby_dsde` package; async work such as exports runs through the private `hirebase_cloud` task service. Look there before concluding that search or scrape behavior is missing from a repo.

Cross-cutting product rules:

* **Origin matters more than the endpoint.** The same API route often costs zero for web-origin (JWT) dashboard browsing and real metered units for API-key calls. Anonymous web gets a first-page tease on many routes; anonymous API is always rejected. This is deliberate. Do not "fix" it by making costs or access uniform across origins.
* **If an endpoint is not in the public docs, treat it as nonexistent.** Remove it rather than fix or enable it.
* **Two billing systems coexist.** Users are `legacy` or `stripe_v2`. Legacy is being sunset, not extended; migrate users off it rather than improving it. The Stripe catalog (`catalog/` in hirebase-api) is the single source of truth for products, prices, features, and meters. Stripe is never edited by hand.
* **HireScout** (`/v2/hirescout`, www.hirescout.org) is a dead product. Do not extend it or treat it as a reference for how Hirebase should work.
* **Vector search is non-public.** `POST /v2/jobs/vsearch` was removed from the docs in September 2026 because Neural Search (`POST /v2/jobs/neural-search`) is better for every use it had: free text via `vector.query`, similar jobs via `vector.job_ids`, resume matching via `vector.artifact_id`, plus lexical filters. Do not document, promote, or extend vsearch; steer customers and the SDK to Neural Search. The route still exists only because the web app calls it.

### Product memory

Maintain this file as you learn important things about how Hirebase is intended to work. Useful things to preserve: the purpose of important features, primary customer use cases, deliberate limitations, important non-goals, architectural tradeoffs, decisions Spencer or John explain, and mistakes or assumptions future Claude sessions are likely to repeat.
Capture the underlying principle rather than the specific incident. Bad: "Remove the vsearch docs page." Better: "Vector search is non-public; Neural Search is the one supported semantic endpoint."
Put cross-repo knowledge in the shared section (and copy it to the other repos); put repo-only knowledge under **This repo**. Use restraint. Do not add temporary task details, obvious facts easily discovered from code, speculative conclusions, minor implementation details, or every correction you receive. If you are uncertain whether something represents a durable product decision, ask before treating it as one.

### Working style

For non-trivial work, briefly establish: desired outcome (what should actually happen), current behavior (what happens now), intent (why this part of the system appears to exist), and the minimum useful change. You do not need to produce a long plan unless one is useful. Investigate enough to make a good decision, then act. The goal is not minimal code at all costs; it is high-impact, low-unnecessary-complexity engineering.

## This repo: hirebase-python-sdk

Public Python client for the Hirebase API, published to PyPI as `hirebase`. Python >= 3.9, src layout, sync and async clients, optional typer CLI (`hirebase`).

* Commands: `pip install -e ".[dev]"`, `pytest` (mocked). Live tests: `HIREBASE_API_KEY=... pytest tests/test_integration.py -v`. Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` if stray plugins interfere. No lint config.
* Release: default branch `main`. Publishing runs only on a GitHub Release (`.github/workflows/release.yml`, PyPI trusted publishing). The version comes from `pyproject.toml`, not the tag, so bump it before cutting a release. There is no CI on push or PR.
* The client is hand-written; request paths are string constants in `src/hirebase/_ops.py`. Auth is the `X-API-Key` header, resolved from the argument, then `HIREBASE_API_KEY`.
* Only wrap endpoints that appear in the public docs (see shared rules). If the docs and the SDK disagree, the docs win.
* Two kinds of 429: `RateLimitError` (per-key request rate, retryable) and `QuotaExceededError` (`X-Billing-Code: limit_exceeded`, backoff will not help). Keep them distinct.
* Deliberate limits worth knowing: `limit` caps at 100, resume uploads at 5 MB, `stream_url` is JSON Lines only, JSON-array exports need the `streaming` extra, unknown filter keys pass through to the API untouched.
