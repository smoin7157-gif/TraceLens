# TraceLens

**TraceLens** is an open-source, self-hostable LLM platform that combines:

1. **Observe & evaluate** — request tracing, span trees, prompt versioning, datasets, evaluators, experiments, feedback, and dashboards (LangSmith / Helicone–class tooling).
2. **Control & optimize** — an OpenAI-compatible gateway with retries, circuit breakers, rate limits, budgets, security checks, exact + semantic caching, prompt compression, and cost-aware routing.

The two halves are designed to **feed each other**: observability scores inform routing; every optimization is measured in traces (tokens and dollars saved).

## Status

| Phase | Description | State |
|-------|-------------|-------|
| 0 | Plan (`PLAN.md`, `PROGRESS.md`) | Done |
| 1 | Foundation & local stack | Done |
| 2–14 | See `PLAN.md` | Planned |

This repo is being built in **14 incremental phases** with tests and CI per phase. See [`PLAN.md`](PLAN.md) for architecture and roadmap; [`PROGRESS.md`](PROGRESS.md) for the live checklist.

## Tech stack

- **Backend:** Python 3.12, FastAPI, httpx, Pydantic v2, SQLAlchemy 2 + Alembic
- **Data:** Postgres (+ pgvector), Redis
- **Dashboard:** Next.js (upcoming phases)
- **Infra:** Docker Compose, GitHub Actions

## Quick start (Phase 1)

**Prerequisites:** Docker Desktop, Python 3.12 (optional, for local dev without Docker API build).

```bash
# Clone and enter the repo
git clone https://github.com/smoin7157-gif/tracelens.git
cd tracelens

# Optional: copy env template
cp .env.example .env

# Start Postgres, Redis, and API
docker compose up --build
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected JSON includes `"status": "ok"` and the API version.

### Local development (backend only)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests && mypy && pytest -q
uvicorn tracelens.main:app --reload
```

## Repository layout

```
backend/          # FastAPI application (tracelens package)
dashboard/        # Next.js UI (later phases)
sdk/              # Python SDK + JS snippet (later phases)
scripts/          # Chaos, benchmark, demo traffic (later phases)
```

## Dogfooding (planned)

Real traffic from **Hire AI** and **Interview OS** will drive benchmarks and `RESULTS.md` numbers in the final phases.

## License

To be added. Open-source intent; license TBD before public release.

## Contributing

Project is in active phased development. After Phase 1, open issues and PRs should target a single phase scope — see `PLAN.md`.