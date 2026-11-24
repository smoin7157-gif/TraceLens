import uuid
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.config import get_settings, load_overlay_dict, reload_settings, save_overlay_dict
from tracelens.config.overlay import overlay_path
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.observe.savings_report import weekly_savings_report

router = APIRouter(prefix="/admin", tags=["admin"])


class OverlayPatchRequest(BaseModel):
    overlay: dict[str, Any] = Field(default_factory=dict)


class OverlayYamlRequest(BaseModel):
    yaml: str = Field(min_length=1)


@router.get("/config")
async def get_runtime_config(_admin: AdminDep) -> dict[str, Any]:
    settings = get_settings()
    return {
        "overlay_path": str(overlay_path()),
        "overlay": load_overlay_dict(),
        "routing": settings.routing.model_dump(),
        "shadow": settings.shadow.model_dump(),
        "circuit_breaker": settings.circuit_breaker.model_dump(),
        "retry": settings.retry.model_dump(),
    }


@router.post("/config/reload")
async def reload_runtime_config(_admin: AdminDep) -> dict[str, object]:
    settings = reload_settings()
    return {
        "reloaded": True,
        "routing_fallback_chains": settings.routing.fallback_chains,
        "shadow": settings.shadow.model_dump(),
    }


@router.put("/config/overlay")
async def replace_overlay(body: OverlayPatchRequest, _admin: AdminDep) -> dict[str, object]:
    path = save_overlay_dict(body.overlay)
    settings = reload_settings()
    return {
        "saved_to": str(path),
        "routing_fallback_chains": settings.routing.fallback_chains,
    }


@router.put("/config/overlay/yaml")
async def replace_overlay_yaml(body: OverlayYamlRequest, _admin: AdminDep) -> dict[str, object]:
    try:
        parsed = yaml.safe_load(body.yaml)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Overlay YAML must be a mapping")
    path = save_overlay_dict(parsed)
    reload_settings()
    return {"saved_to": str(path), "overlay_keys": list(parsed.keys())}


async def _require_tenant(session: SessionDep, tenant_id: uuid.UUID) -> None:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.get("/tenants/{tenant_id}/reports/savings")
async def tenant_weekly_savings(
    tenant_id: uuid.UUID,
    session: SessionDep,
    _admin: AdminDep,
    days: int = 7,
) -> dict[str, object]:
    await _require_tenant(session, tenant_id)
    return await weekly_savings_report(session, tenant_id, days=days)
