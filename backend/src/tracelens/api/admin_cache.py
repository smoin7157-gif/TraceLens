import uuid

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.config import get_settings
from tracelens.db.models.semantic_cache import SemanticCacheEntry
from tracelens.db.redis_client import RedisClient
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.optimize.cache import exact_cache_key

router = APIRouter(prefix="/admin", tags=["admin"])


class CachePurgeRequest(BaseModel):
    model: str = Field(min_length=1, max_length=128)
    digest: str | None = Field(default=None, min_length=64, max_length=64)


@router.delete("/tenants/{tenant_id}/cache/exact", status_code=status.HTTP_200_OK)
async def purge_exact_cache(
    tenant_id: uuid.UUID,
    body: CachePurgeRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, object]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    redis = RedisClient.connection()
    if body.digest:
        deleted = int(await redis.delete(exact_cache_key(tenant_id, body.model, body.digest)))
        return {"deleted_keys": deleted, "scope": "single"}
    pattern = f"tl:cache:exact:{tenant_id}:{body.model}:*"
    deleted = 0
    async for key in redis.scan_iter(match=pattern, count=200):
        deleted += int(await redis.delete(key))
    return {"deleted_keys": deleted, "scope": "model"}


@router.delete("/tenants/{tenant_id}/cache/semantic", status_code=status.HTTP_200_OK)
async def purge_semantic_cache(
    tenant_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
    model: str | None = Query(default=None),
) -> dict[str, object]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    stmt = delete(SemanticCacheEntry).where(SemanticCacheEntry.tenant_id == tenant_id)
    if model:
        stmt = stmt.where(SemanticCacheEntry.model == model)
    result = await session.execute(stmt)
    return {"deleted_rows": result.rowcount or 0}


@router.get("/tenants/{tenant_id}/cache/semantic/stats")
async def semantic_cache_stats(
    tenant_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, object]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    stmt = select(
        func.count(SemanticCacheEntry.id),
        func.count(func.distinct(SemanticCacheEntry.model)),
    ).where(SemanticCacheEntry.tenant_id == tenant_id)
    total, models = (await session.execute(stmt)).one()
    settings = get_settings()
    return {
        "tenant_id": str(tenant_id),
        "entry_count": int(total or 0),
        "distinct_models": int(models or 0),
        "similarity_threshold": settings.cache.semantic_similarity_threshold,
    }


@router.get("/tenants/{tenant_id}/cache/exact/stats")
async def exact_cache_stats(
    tenant_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
    model: str | None = Query(default=None),
) -> dict[str, object]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    redis = RedisClient.connection()
    pattern = f"tl:cache:exact:{tenant_id}:{model or '*'}:*"
    count = 0
    async for _ in redis.scan_iter(match=pattern, count=200):
        count += 1
    return {"tenant_id": str(tenant_id), "model_filter": model, "key_count_estimate": count}