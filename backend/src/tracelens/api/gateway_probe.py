from fastapi import APIRouter

from tracelens.api.deps import GatewayContextDep

router = APIRouter(tags=["gateway"])


@router.get("/v1/whoami")
async def whoami(context: GatewayContextDep) -> dict[str, str]:
    """Authenticated probe: proves bearer resolution (replaced by real gateway in phase 4)."""
    assert context.tenant_id is not None and context.key_id is not None
    return {
        "tenant_id": str(context.tenant_id),
        "key_id": str(context.key_id),
    }
