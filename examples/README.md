# Hirebase SDK — Example workflows

Runnable scripts that show how different teams use the API. Each script prints clear
section markers so you can follow what is happening step by step.

## Setup

```bash
# Clone the repo locally to get the examples/
git clone https://github.com/hirebase-1/hirebase-python-sdk && cd hirebase-python-sdk/

# Install from source is easiest, plus allows you to modify and debug your queries better
pip install -e ".[dev]" 

# API key required for all examples (base URL defaults to https://api.hirebase.org)
export HIREBASE_API_KEY="hb_..."
# or put HIREBASE_API_KEY=... in .env at the repo root
```

## Sample resume

Several examples download a public PDF resume (not a real candidate — fine for demos):

https://pjreddie.com/static/resume.pdf <-- the creator of the YOLO model (AI object detector) has a quirky resume that has been publically available for years, we will use this to demonstrate the Resume API

## Workflows

| Script | Audience | What it demonstrates |
|--------|----------|----------------------|
| [01_job_board_search.py](./01_job_board_search.py) | Job board developers | Lexical job search + pagination |
| [02_job_board_neural_match.py](./02_job_board_neural_match.py) | Job board developers | Hybrid neural search (semantic + filters) |
| [03_sales_company_prospecting.py](./03_sales_company_prospecting.py) | Sales / GTM | Company research → tech/skills insights → outreach list |
| [04_analyst_market_insights.py](./04_analyst_market_insights.py) | Market analysts | Cohort insights (salary, remote %, top tech) |
| [05_data_engineer_export_stream.py](./05_data_engineer_export_stream.py) | Data engineers | Export task → poll → download → stream JSONL |
| [06_recruiter_resume_match.py](./06_recruiter_resume_match.py) | Recruiters | Upload + parse resume → match jobs |
| [07_enterprise_embed_vectors.py](./07_enterprise_embed_vectors.py) | ML / enterprise | Private embed (no storage) → vector search |
| [08_company_hiring_intel.py](./08_company_hiring_intel.py) | Competitive intel | Company-scoped hiring insights |
| [09_async_pipeline.py](./09_async_pipeline.py) | Platform engineers | Same search flow with `AsyncClient` |

## Run one example

```bash
python examples/01_job_board_search.py
```

## Notes

- **Export** (`05`) meters by job count — keep `limit` low while testing.
- **Enterprise embed** (`07`) needs an API key with commercial embed permission; you may see 403 on a standard key.
- **All search APIs** and **insights** may require a paid plan depending on your key.

## Need help?

If you run into any issues setting up or running the example workflows, feel free to email [spencer@hirebase.org](mailto:spencer@hirebase.org) for quick help and debugging support.