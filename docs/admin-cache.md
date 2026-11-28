# Admin cache and trace DLQ APIs

All routes require `Authorization: Bearer $ADMIN_API_TOKEN`.

## Exact cache (Redis)

- `DELETE /admin/tenants/{id}/cache/exact` — body `{ "model", "digest"? }`; omit `digest` to purge all keys for the model.
- `GET /admin/tenants/{id}/cache/exact/stats?model=` — approximate key count via `SCAN`.

## Semantic cache (Postgres + pgvector)

- `DELETE /admin/tenants/{id}/cache/semantic?model=` — delete rows; optional model filter.
- `GET /admin/tenants/{id}/cache/semantic/stats` — entry counts and similarity threshold.

## Trace ingestion DLQ

- `GET /admin/observe/trace-dlq?limit=10` — sample failed trace payloads.
- `POST /admin/observe/trace-dlq/requeue` — body `{ "count": 1 }` moves items from DLQ back to the main queue.