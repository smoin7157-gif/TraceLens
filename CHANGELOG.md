# Changelog

## Unreleased

### Security

- SSRF-safe validation for alert and budget webhook URLs; block link-local and metadata hosts.

### Performance

- Semantic cache lookups use pgvector cosine distance with HNSW index (migration `009`).
- Semantic cache writes upsert on `(tenant_id, model, request_hash)`.

### Operations

- Admin APIs: purge exact/semantic cache, cache stats, trace DLQ peek/requeue.
- Prometheus: `tracelens_cache_lookup_total`, `tracelens_trace_dlq_total`.
- Observe DB indexes (migration `010`).
- Dashboard Vercel deployment guide (`docs/vercel.md`).