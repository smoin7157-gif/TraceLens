# TraceLens — Results & proof

> **Policy:** Numbers in this file must come from **real dogfood traffic** (Hire AI, Interview OS, or your production pilot). Do not fabricate benchmarks.

## 60-second pitch (template)

TraceLens is a self-hosted LLM gateway plus observability stack. It adds **cost-aware routing, caching, and budgets** on the hot path while capturing **traces, experiments, and eval scores** for feedback into routing. You run one compose stack; clients keep using the OpenAI API shape.

## Resume bullets (fill with your metrics)

- Reduced LLM spend by **\_%** over **\_ weeks** via semantic/exact cache + safe downgrade routing (source: `GET /admin/tenants/{id}/reports/savings`).
- Improved p95 gateway overhead to **\_ ms** ex-provider on **\_ RPS** (source: `scripts/benchmark.py` + Prometheus).
- Zero user-visible errors during provider chaos test (**\_/\_** requests succeeded with fallback) — `scripts/chaos_provider.py`.

## Benchmark table (paste output from `python scripts/benchmark.py`)

| Metric | Value | Date | Environment |
|--------|-------|------|-------------|
| p50_ms | _TBD_ | | |
| p95_ms | _TBD_ | | |
| Requests | _TBD_ | | |

## Weekly savings (paste JSON from admin report)

```json
{
  "request_count": "TBD",
  "savings_usd": "TBD",
  "period_days": 7
}
```

## Chaos / resilience demo

```bash
export TRACELENS_API_KEY=...
python scripts/chaos_provider.py --attempts 12
```

Expected: **12/12 HTTP 200** with `mock-gpt-4` (or chain second candidate) selected when `mock-gpt` fails.

## Dogfood integrations

- [Hire AI](docs/integrations/hire-ai.md)
- [Interview OS](docs/integrations/interview-os.md)