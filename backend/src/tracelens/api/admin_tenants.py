import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.db.repositories.tenant import TenantRepository

router = APIRouter(prefix="/admin", tags=["admin"])


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> TenantResponse:
    repo = TenantRepository(session)
    existing = await repo.get_by_slug(body.slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")
    tenant = await repo.create(name=body.name, slug=body.slug)
    return TenantResponse(id=tenant.id, name=tenant.name, slug=tenant.slug)


@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(
    _admin: AdminDep,
    session: SessionDep,
    limit: int = 100,
) -> list[TenantResponse]:
    tenants = await TenantRepository(session).list_recent(limit=limit)
    return [TenantResponse(id=t.id, name=t.name, slug=t.slug) for t in tenants]
