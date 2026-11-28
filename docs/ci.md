# CI overview

GitHub Actions run backend lint, typecheck, unit tests, and dashboard `npm run build` on each push to `main`.

After merging platform changes, confirm:

- `alembic upgrade head` on staging (migrations `009`–`010` for semantic HNSW and observe indexes)
- Prometheus shows `tracelens_cache_lookup_total` after traffic
- Vercel preview uses `NEXT_PUBLIC_TRACELENS_API_URL` pointing at a CORS-allowed API