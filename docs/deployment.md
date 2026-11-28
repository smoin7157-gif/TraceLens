# Deployment guide

## Minimum production settings

| Variable | Purpose |
|----------|---------|
| `APP_ENV=production` | Disables OpenAPI UI |
| `ADMIN_API_TOKEN` | Admin + demo seed |
| `METRICS_SCRAPE_TOKEN` | Optional bearer for `/metrics` |
| `DASHBOARD_READ_TOKEN` | Optional bearer for `/dashboard/*` (except SSE live) |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `DATABASE_URL` / `REDIS_URL` | Managed services |

## Health checks

- **Liveness:** `GET /health`
- **Readiness:** `GET /health/ready` (Postgres + Redis)

## Migrations

Run before traffic:

```bash
cd backend && alembic upgrade head
```

Docker entrypoint runs migrations automatically when using the provided `docker-entrypoint.sh`.

## Metrics

Protect Prometheus scrapes:

```bash
curl -H "Authorization: Bearer $METRICS_SCRAPE_TOKEN" http://api:8000/metrics
```

## Dashboard (Vercel)

The Next.js UI can deploy to Vercel with project root `dashboard`. Point `NEXT_PUBLIC_TRACELENS_API_URL` at your API and allow the Vercel origin in `CORS_ORIGINS`. Full steps: [`vercel.md`](vercel.md).