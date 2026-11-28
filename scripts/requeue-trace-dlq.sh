#!/usr/bin/env bash
# Requeue up to N traces from the trace DLQ (requires ADMIN_API_TOKEN).
set -euo pipefail
COUNT="${1:-1}"
API="${TRACELENS_API_URL:-http://localhost:8000}"
curl -fsS -X POST "$API/admin/observe/trace-dlq/requeue" \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN:?}" \
  -H "Content-Type: application/json" \
  -d "{\"count\": ${COUNT}}"