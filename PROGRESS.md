# TraceLens — Progress Log

## Phase checklist

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Foundation & local stack | ✅ Done | 2025-11-21 |
| 2 | Data layer & tenant isolation | ✅ Done | 2025-11-21 |
| 3 | API keys & auth pipeline stage | ⬜ Not started | — |
| 4 | Pipeline framework & MOCK gateway | ⬜ Not started | — |
| 5 | Multi-provider adapters & models | ⬜ Not started | — |
| 6 | Streaming SSE | ⬜ Not started | — |
| 7 | Rate limits, validation, security scan | ⬜ Not started | — |
| 8 | Health, breaker, retries, fallback | ⬜ Not started | — |
| 9 | Budgets & economics row | ⬜ Not started | — |
| 10 | Caching & cost optimization | ⬜ Not started | — |
| 11 | Observability core & Python SDK | ⬜ Not started | — |
| 12 | Prompts, datasets, evaluators, alerts | ⬜ Not started | — |
| 13 | Dashboard (Next.js) | ⬜ Not started | — |
| 14 | Differentiators, dogfooding, proof & docs | ⬜ Not started | — |

**Legend:** ⬜ Not started · 🔄 In progress · ✅ Done · ⏸ Blocked

---

## Session log

### Phase 2 — Data layer & tenant isolation — 2025-11-21

**Goal (3 lines):**
- SQLAlchemy 2 models for `tenants`, `api_keys`, `traces`, `spans` with Postgres + pgvector extension enabled.
- Async engine/session helpers and Alembic migration `001`.
- `TenantScopedRepository` plus Redis pool helper; isolation enforced in tests.

**Built:**
- `backend/src/tracelens/db/**` (models, session, redis_client, repositories).
- `backend/alembic/versions/001_initial.py`, `tests/unit/test_tenant_isolation.py`, CI Postgres service.

**Verify:**
- Default: `cd backend && pytest -q` (unit tests; integration skipped).
- With Postgres: `TRACELENS_INTEGRATION_TESTS=1` + `docker compose up postgres` → `pytest -q` (6 tests).

**Interview talking point:**
- **Repository-layer tenant scoping** vs RLS only: every query goes through `TenantScopedRepository` with mandatory `tenant_id` so bugs fail in Python tests without DB policy magic; tradeoff is you must route all data access through repos (discipline, not a silver bullet).

**Tests:** ruff ✅ / mypy ✅ / pytest ✅ (3 unit + 3 integration in CI)

---

### Phase 1 — Foundation & local stack — 2025-11-21

(See prior entry in git history.)

---

## Notes / reorder requests

- (empty)