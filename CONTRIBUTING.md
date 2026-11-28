# Contributing to TraceLens

## Setup

```bash
cd backend
python -m venv .venv
pip install -e ".[dev]"
export TRACELENS_CONFIG_OVERLAY_PATH=../config/overlay.yaml
```

Integration tests need Postgres + Redis:

```bash
export TRACELENS_INTEGRATION_TESTS=1
docker compose up -d postgres redis
pytest -q
```

## Quality gates

```bash
ruff check src tests && ruff format --check src tests && mypy && pytest -q
```

Dashboard:

```bash
cd dashboard && npm install && npm run typecheck && npm run build
```

## Scope

- Target **one concern per PR** when possible (matches phased `PLAN.md` history)
- Include tests for behavior changes
- Do not commit `.env` or secrets