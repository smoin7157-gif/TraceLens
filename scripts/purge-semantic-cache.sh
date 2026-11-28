#!/usr/bin/env bash
# Purge semantic cache rows for a tenant (optional ?model= query).
set -euo pipefail
TENANT_ID="${1:?tenant uuid}"
API="${TRACELENS_API_URL:-http://localhost:8000}"
MODEL="${2:-}"
QS=""
if [[ -n "$MODEL" ]]; then
  QS="?model=${MODEL}"
fi
curl -fsS -X DELETE "$API/admin/tenants/${TENANT_ID}/cache/semantic${QS}" \
  -H "Authorization: Bearer ${ADMIN_API_TOKEN:?}"