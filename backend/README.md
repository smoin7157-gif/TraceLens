# TraceLens backend

Python 3.12 FastAPI gateway and observability API. Install locally:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"
pytest

# Integration tests (requires Postgres, e.g. docker compose up postgres)
set TRACELENS_INTEGRATION_TESTS=1
alembic upgrade head
pytest -q -m integration
```