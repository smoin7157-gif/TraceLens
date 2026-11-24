# Hire AI → TraceLens

Point Hire AI’s OpenAI-compatible client at TraceLens instead of a vendor endpoint.

## Environment

```bash
OPENAI_BASE_URL=http://tracelens-api:8000/v1
OPENAI_API_KEY=tl_...   # issued via POST /admin/tenants/{id}/keys
```

## Recommended headers

| Header | Purpose |
|--------|---------|
| `X-TraceLens-Model-Override` | Pin a model for A/B without client changes |
| `X-TraceLens-Shadow-Sync: 1` | Dev-only: await shadow model comparison |

## Observability

- Traces appear after `trace_worker` drains Redis (`/dashboard/traces`).
- Economics land in `requests_log`; import rows into datasets for eval (`POST /admin/tenants/{id}/datasets/import`).

## Savings proof

Export weekly rollup for dashboards or finance:

```bash
curl -H "X-Admin-Token: $ADMIN_API_TOKEN" \
  "http://localhost:8000/admin/tenants/{tenant_id}/reports/savings?days=7"
```

Paste the JSON into `RESULTS.md` when running real Hire AI traffic.