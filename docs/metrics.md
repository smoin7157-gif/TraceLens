# Prometheus metrics

Scrape `GET /metrics` (optionally with `METRICS_SCRAPE_TOKEN`).

| Metric | Labels | Meaning |
|--------|--------|---------|
| `tracelens_gateway_requests_total` | `outcome` | Chat completions by pipeline outcome |
| `tracelens_trace_enqueue_total` | `result` | Trace queue push results |
| `tracelens_trace_worker_processed_total` | `result` | Worker persistence |
| `tracelens_eval_worker_processed_total` | `result` | Eval worker |
| `tracelens_cache_lookup_total` | `kind` | `exact`, `semantic`, `miss`, `bypass` |
| `tracelens_trace_dlq_total` | — | Items pushed to trace DLQ after persist failure |