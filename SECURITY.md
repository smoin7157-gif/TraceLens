# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main`  | Yes       |

## Reporting a vulnerability

Please **do not** open public GitHub issues for security-sensitive bugs.

Email maintainers with:

- Description and impact
- Steps to reproduce
- Affected commit or release tag

We aim to acknowledge reports within 72 hours.

## Operational hardening checklist

- Set strong `ADMIN_API_TOKEN` and rotate regularly
- Set `METRICS_SCRAPE_TOKEN` if Prometheus scrapes `/metrics`
- Set `DASHBOARD_READ_TOKEN` if the dashboard BFF is exposed beyond localhost
- Use TLS at the edge; restrict Postgres/Redis to private networks
- Keep `MOCK` providers disabled in production (`APP_ENV=production`)