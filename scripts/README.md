# Operational scripts

| Script | Purpose |
|--------|---------|
| `requeue-trace-dlq.sh` | Move failed traces from Redis DLQ back to the worker queue |
| `purge-semantic-cache.sh` | DELETE admin semantic cache for a tenant |

Requires `ADMIN_API_TOKEN` and `TRACELENS_API_URL`.