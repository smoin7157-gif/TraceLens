# Hosting the dashboard on Vercel

The TraceLens **API** (FastAPI, Postgres, Redis, workers) should run on Docker, Kubernetes, or a VM. The **Next.js dashboard** is a good fit for [Vercel](https://vercel.com).

## 1. Connect the repository

- **Root directory:** `dashboard`
- **Framework preset:** Next.js
- **Production branch:** `main`

Use the Vercel Git integration with `smoin7157-gif/TraceLens` or import the same repo manually.

## 2. Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_TRACELENS_API_URL` | Yes | Public base URL of your API (e.g. `https://api.example.com`) |
| `NEXT_PUBLIC_DASHBOARD_TOKEN` | If API uses gate | Same value as `DASHBOARD_READ_TOKEN` on the API |

Set these in **Project → Settings → Environment Variables** for Production and Preview.

## 3. CORS on the API

Add your Vercel hostname to `CORS_ORIGINS` on the API, for example:

```text
https://tracelens-dashboard.vercel.app
```

## 4. What is not on Vercel

- Postgres, Redis, Alembic migrations
- Trace/eval workers and Prometheus `/metrics`

Run those alongside the API using `docker-compose.yml` or your orchestrator. See [`deployment.md`](deployment.md).