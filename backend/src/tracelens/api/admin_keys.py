import uuid

from fastapi import APIRouter, HTTPException, status

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.api.schemas import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyListItem
from tracelens.db.repositories.api_key import ApiKeyRepository
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.security.keys import issue_api_key

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/tenants/{tenant_id}/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    tenant_id: uuid.UUID,
    body: ApiKeyCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> ApiKeyCreateResponse:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    material = issue_api_key()
    record = await ApiKeyRepository(session, tenant_id).create(
        key_hash=material.key_hash,
        key_prefix=material.key_prefix,
        name=body.name,
        scopes=body.scopes,
        allowed_models=body.allowed_models,
    )
    return ApiKeyCreateResponse(
        id=record.id,
        tenant_id=record.tenant_id,
        name=record.name,
        key_prefix=record.key_prefix,
        secret=material.raw_key,
        scopes=record.scopes,
        allowed_models=record.allowed_models,
        created_at=record.created_at,
    )


@router.get("/tenants/{tenant_id}/api-keys", response_model=list[ApiKeyListItem])
async def list_api_keys(
    tenant_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> list[ApiKeyListItem]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    keys = await ApiKeyRepository(session, tenant_id).list_keys()
    return [
        ApiKeyListItem(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=key.scopes,
            allowed_models=key.allowed_models,
            created_at=key.created_at,
            revoked_at=key.revoked_at,
        )
        for key in keys
    ]


@router.delete("/tenants/{tenant_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> None:
    revoked = await ApiKeyRepository(session, tenant_id).revoke(key_id)
    if revoked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
