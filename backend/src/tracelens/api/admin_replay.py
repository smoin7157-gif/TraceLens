import uuid

from fastapi import APIRouter, HTTPException, Request, status

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.db.repositories.request_log import RequestLogRepository
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.observe.replay import (
    build_chat_request_from_log,
    diff_replay,
    extract_logged_response_text,
)
from tracelens.providers.registry import ProviderRegistry

router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_tenant(session: SessionDep, tenant_id: uuid.UUID) -> None:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.post("/tenants/{tenant_id}/replay/{request_log_id}")
async def replay_request_log(
    tenant_id: uuid.UUID,
    request_log_id: uuid.UUID,
    request: Request,
    session: SessionDep,
    _admin: AdminDep,
) -> dict[str, object]:
    await _require_tenant(session, tenant_id)
    repo = RequestLogRepository(session, tenant_id)
    row = await repo.get_by_id(request_log_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Request log not found")
    try:
        chat_request = build_chat_request_from_log(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    registry = ProviderRegistry(session)
    replay_response = await registry.chat_completion(
        chat_request,
        http_request=request,
        completion_id=f"replay-{row.request_id}",
    )
    original = extract_logged_response_text(row)
    comparison = diff_replay(original_text=original, replay_response=replay_response)
    return {
        "request_log_id": str(row.id),
        "request_id": row.request_id,
        "comparison": comparison,
        "routing_explanation": row.routing_explanation,
    }
