# TraceLens — Progress Log

## Phase checklist

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Foundation & local stack | ✅ Done | 2025-11-21 |
| 2 | Data layer & tenant isolation | ✅ Done | 2025-11-21 |
| 3 | API keys & auth pipeline stage | ✅ Done | 2025-11-21 |
| 4 | Pipeline framework & MOCK gateway | ✅ Done | 2025-11-21 |
| 5 | Multi-provider adapters & models | ✅ Done | 2025-11-22 |
| 6 | Streaming SSE | ✅ Done | 2025-11-22 |
| 7 | Rate limits, validation, security scan | ✅ Done | 2025-11-22 |
| 8 | Health, breaker, retries, fallback | ✅ Done | 2025-11-22 |
| 9 | Budgets & economics row | ✅ Done | 2025-11-22 |
| 10 | Caching & cost optimization | ✅ Done | 2025-11-22 |
| 11 | Observability core & Python SDK | ✅ Done | 2025-11-22 |
| 12 | Prompts, datasets, evaluators, alerts | ✅ Done | 2025-11-22 |
| 13 | Dashboard (Next.js) | ⬜ Not started | — |
| 14 | Differentiators, dogfooding, proof & docs | ⬜ Not started | — |

**Legend:** ⬜ Not started · 🔄 In progress · ✅ Done · ⏸ Blocked

---

## Session log

### Phase 12 — Prompts, datasets, experiments, evaluators, alerts — 2025-11-22

**Goal (3 lines):**
- Versioned prompts with compare API + rolling eval metrics.
- Datasets from `requests_log`; experiment runner with side-by-side variant scores.
- Async eval worker (regex/JSON schema); alerts with webhooks; eval scores feed router.

**Built:**
- Migration `006`, `observe/*`, `workers/eval_worker.py`, admin observe APIs, `eval-worker` compose.

**Verify:**
- `pytest -q tests/unit/test_evaluators.py tests/unit/test_routing_quality.py tests/integration/test_experiment_flow.py`

**Interview talking point:**
- **Eval scores in Redis for routing**: batch eval writes `tl:quality:{tenant}:{model}` so the router weights quality without blocking chat; tradeoff is eventually-consistent scores until the worker runs.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 11 — Observability core & Python SDK — 2025-11-22

**Goal (3 lines):**
- Async trace enqueue to Redis; worker persists trace + span trees in Postgres.
- Prometheus `/metrics`; structured JSON logging; W3C `traceparent` on gateway responses.
- Python SDK: `trace_span` context manager + `@traced` decorator with child spans.

**Built:**
- `observe/traces.py`, `trace_queue.py`, `persistence.py`, `metrics.py`, `workers/trace_worker.py`.
- `sdk/python/tracelens_sdk/`; compose `trace-worker` service.

**Verify:**
- `pytest -q tests/unit/test_trace_queue.py tests/unit/test_sdk_spans.py tests/unit/test_metrics_endpoint.py`

**Interview talking point:**
- **Fail-open enqueue + async worker**: gateway only LPUSHes JSON — if Redis blips, request still succeeds; worker owns durability; tradeoff is seconds of lag before traces appear in Postgres.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 10 — Caching & cost optimization — 2025-11-22

**Goal (3 lines):**
- Exact Redis cache + pgvector semantic cache (tenant-scoped, ≥0.92 similarity).
- Optimizer: history trim + whitespace compress; safe-downgrade routing + model override header.
- Full savings columns: `cost_without_optimization - cost_actual` in `requests_log` and response.

**Built:**
- `optimize/cache.py`, `semantic.py`, `compress.py`, `cost.py`, `embeddings/backends/minilm.py`.
- `CacheLookupStage`, `CacheWriteStage`, `OptimizerStage`; migration `005_semantic_cache`.

**Verify:**
- `pytest -q tests/unit/test_exact_cache.py tests/unit/test_savings_math.py tests/unit/test_semantic_similarity.py`
- Integration: `test_semantic_cache_isolation.py` (Postgres)

**Interview talking point:**
- **Exact-before-semantic ladder**: SHA-keyed Redis for identical prompts, then pgvector for near-dups — skips provider only after tenant-scoped lookup; tradeoff is embedding cost on miss vs zero marginal cost on hit.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 9 — Budgets & economics row — 2025-11-22

**Goal (3 lines):**
- Per-key daily/monthly token (and USD) caps in Redis with PG `budgets` + `requests_log`.
- Hard stop before provider (`insufficient_quota`); 80% threshold webhooks (deduped).
- Economics skeleton persisted on every completed gateway call (costs `0` until phase 10).

**Built:**
- `security/budgets.py`, `observe/request_log.py`, `pipeline/stages/budget.py`, `request_log.py`.
- Migration `004` (`budgets`, `requests_log`, `api_keys.budget_id`); admin budget APIs.

**Verify:**
- `pytest -q tests/unit/test_budget_counters.py tests/unit/test_request_log_economics.py`

**Interview talking point:**
- **Redis counters for speed, PG rows for audit**: hot path only does O(1) INCRBY; durable economics live in `requests_log` for later cache/savings math; tradeoff is dual writes until reconcile job (stubbed) lands.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 8 — Health, circuit breaker, retries, fallback — 2025-11-22

**Goal (3 lines):**
- Redis rolling stats per provider/model; circuit breaker (closed/open/half-open).
- Jittered exponential retries honoring `Retry-After`; `RouterStage` + fallback chains.
- `GET /health/providers`; chat responses include `routing_explanation`.

**Built:**
- `resilience/circuit_breaker.py`, `provider_stats.py`, `optimize/routing.py`, `providers/retry.py`.
- `pipeline/stages/router.py`, `provider_call.py`; `gateway/health.py`; resilience config on `Settings`.

**Verify:**
- `pytest -q tests/unit/test_circuit_breaker.py tests/unit/test_provider_retry.py tests/unit/test_routing_plan.py tests/unit/test_provider_health.py`

**Interview talking point:**
- **Separate router from provider call**: routing reads stats and orders candidates without I/O to vendors; the provider stage owns breaker, retry, and fallback so you can tune resilience without re-running policy logic; tradeoff is two pipeline hops vs one monolithic stage.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 7 — Rate limits, validation, security — 2025-11-22

**Goal (3 lines):**
- Redis sliding-window limits per API key + per IP (tenant-scoped keys).
- Request validation: payload size, max_tokens cap, per-key model allow-list.
- Injection heuristics + PII block/redact/log-only with fail-open/closed policy.

**Built:**
- `security/rate_limit.py`, `validation.py`, `injection.py`, `pii.py` + pipeline stages.
- OpenAI-style 429 for rate limits; CI Redis service.

**Verify:**
- `pytest -q tests/unit/test_rate_limit.py tests/unit/test_security_scan.py tests/unit/test_validation_stage.py`

**Interview talking point:**
- **Tenant-prefixed Redis keys** (`tl:rl:tenant:{id}:...`) so limiter state never shares namespaces across tenants even if key IDs collide in tests; tradeoff is slightly longer keys vs accidental cross-tenant coupling.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 7 — Rate limits, validation, security — 2025-11-22

**Goal (3 lines):**
- Redis sliding-window limits per API key + per IP (tenant-scoped keys).
- Request validation: payload size, max_tokens cap, per-key model allow-list.
- Injection heuristics + PII block/redact/log-only with fail-open/closed policy.

**Built:**
- `security/rate_limit.py`, `validation.py`, `injection.py`, `pii.py` + pipeline stages.
- OpenAI-style 429 for rate limits; CI Redis service.

**Verify:**
- `pytest -q tests/unit/test_rate_limit.py tests/unit/test_security_scan.py tests/unit/test_validation_stage.py`

**Interview talking point:**
- **Tenant-prefixed Redis keys** (`tl:rl:tenant:{id}:...`) so limiter state never shares namespaces across tenants even if key IDs collide in tests; tradeoff is slightly longer keys vs accidental cross-tenant coupling.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 6 — Streaming SSE — 2025-11-22

**Goal (3 lines):**
- `stream: true` returns OpenAI-style SSE (`chat.completion.chunk` + `data: [DONE]`).
- MOCK + OpenAI passthrough streaming; Anthropic/Gemini chunked via normalized adapter.
- Client disconnect stops emission; trace enqueue runs after stream completes.

**Built:**
- `gateway/streaming.py`, stream path in `gateway/chat.py`, provider stream methods, retry placeholder.

**Verify:**
- `pytest -q tests/unit/test_streaming.py tests/unit/test_openai_stream.py`
- Integration: `test_chat_stream.py` with API key + `stream: true`

**Interview talking point:**
- **Defer `trace_enqueue` until after SSE completes**: logging must not block first token, but you still want one enqueue per request — run trace stage in the generator `finally` block; tradeoff is slightly more complex control flow vs duplicating trace logic outside the pipeline.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 5 — Multi-provider adapters & models — 2025-11-22

**Goal (3 lines):**
- OpenAI, Anthropic, and Gemini adapters normalize to internal `ChatCompletionResponse`.
- `GET /v1/models` lists mock + configured providers; chat routes by model prefix.
- Fernet-encrypted credentials in `providers` table with env key fallback.

**Built:**
- `providers/openai.py`, `anthropic.py`, `gemini.py`, `registry.py`, `gateway/models.py`, migration `003`.

**Verify:**
- `pytest -q tests/unit/test_provider_adapters.py` (respx mocks).
- Set `OPENAI_API_KEY` locally for live calls (optional).

**Interview talking point:**
- **Env keys for dev, encrypted DB for prod**: operators bootstrap with `.env`; production stores Fernet blobs so a DB leak doesn’t expose plaintext vendor keys — tradeoff is you must manage `MASTER_ENCRYPTION_KEY` rotation carefully.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 4 — Pipeline framework & MOCK gateway — 2025-11-21

**Goal (3 lines):**
- Ordered toggleable `Pipeline` (`auth` → `provider` → `trace_enqueue`).
- `POST /v1/chat/completions` for `mock-*` models; OpenAI-shaped JSON responses.
- MOCK provider with latency/error-rate/429 simulation via headers + seeded RNG.

**Built:**
- `pipeline/executor.py`, `providers/mock.py`, `gateway/chat.py`, `observe/trace_queue.py` stub.

**Verify:**
- `pytest -q tests/unit/test_pipeline.py tests/unit/test_mock_provider.py`
- With Postgres + API key: integration `test_chat_mock.py`.

**Interview talking point:**
- **Pipeline as explicit stage list + toggles** instead of deep middleware stacks: order is visible in code/tests, features disable without reorder bugs; tradeoff is more boilerplate per stage vs Django-style middleware magic.

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

### Phase 3 — API keys & auth pipeline stage — 2025-11-21

**Goal (3 lines):**
- Admin API to create/list/revoke tenant API keys; only Argon2 hashes stored.
- `AuthStage` resolves `Authorization: Bearer` to `tenant_id` + `key_id` on `GatewayContext`.
- OpenAI-shaped 401 errors; `GET /v1/whoami` probe for verification.

**Built:**
- `security/keys.py`, `pipeline/stages/auth.py`, `api/admin_keys.py`, migration `002`.
- `argon2-cffi` dependency; `ADMIN_API_TOKEN` for admin routes.

**Verify:**
- `pytest -q` (unit auth tests need no DB).
- With Postgres: set `ADMIN_API_TOKEN`, migrate, integration test creates key → `/v1/whoami`.

**Interview talking point:**
- **Prefix + Argon2 verify** instead of storing plaintext or naive single-row lookup: prefix narrows candidates; Argon2 resists offline cracking if DB leaks; tradeoff is O(k) verifications per prefix collision (k tiny with 8-hex prefix).

**Tests:** ruff ✅ / mypy ✅ / pytest ✅

---

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