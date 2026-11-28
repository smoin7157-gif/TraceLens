from typing import Any

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from tracelens.api.deps import AdminDep
from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient

router = APIRouter(prefix="/admin", tags=["admin"])


class TraceDlqRequeueRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=500)


@router.get("/observe/trace-dlq")
async def peek_trace_dlq(
    _admin: AdminDep,
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, Any]:
    settings = get_settings().observe
    redis = RedisClient.connection()
    dlq_key = f"{settings.trace_queue_key}:dlq"
    length = await redis.llen(dlq_key)
    items = await redis.lrange(dlq_key, 0, limit - 1)
    decoded = [item.decode() if isinstance(item, bytes) else str(item) for item in items]
    return {"dlq_key": dlq_key, "length": int(length), "sample": decoded}


@router.post("/observe/trace-dlq/requeue", status_code=status.HTTP_200_OK)
async def requeue_trace_dlq(
    body: TraceDlqRequeueRequest,
    _admin: AdminDep,
) -> dict[str, int]:
    settings = get_settings().observe
    redis = RedisClient.connection()
    dlq_key = f"{settings.trace_queue_key}:dlq"
    queue_key = settings.trace_queue_key
    moved = 0
    for _ in range(body.count):
        raw = await redis.rpop(dlq_key)
        if raw is None:
            break
        await redis.lpush(queue_key, raw)
        moved += 1
    return {"requeued": moved, "remaining": int(await redis.llen(dlq_key))}