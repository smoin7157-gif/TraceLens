import asyncio
import time
import uuid
from uuid import UUID

from redis.asyncio import Redis

from tracelens.config import get_settings


def rate_limit_key_for_api_key(tenant_id: UUID, key_id: UUID) -> str:
    return f"tl:rl:tenant:{tenant_id}:key:{key_id}"


def rate_limit_key_for_ip(tenant_id: UUID, ip_address: str) -> str:
    return f"tl:rl:tenant:{tenant_id}:ip:{ip_address}"


class SlidingWindowRateLimiter:
    """Redis sorted-set sliding window (per PLAN: sliding window per key + per IP)."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def allow(self, redis_key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        member = f"{now}:{uuid.uuid4().hex}"
        window_start = now - window_seconds

        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(redis_key, "-inf", window_start)
            pipe.zadd(redis_key, {member: now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_seconds + 5)
            removed, _, count, _ = await pipe.execute()

        _ = removed
        remaining = max(0, limit - int(count))
        return int(count) <= limit, remaining


async def check_rate_limits(
    redis: Redis,
    *,
    tenant_id: UUID,
    key_id: UUID,
    client_ip: str | None,
) -> tuple[bool, str | None]:
    settings = get_settings()
    policy = settings.rate_limit
    limiter = SlidingWindowRateLimiter(redis)

    key_rl = rate_limit_key_for_api_key(tenant_id, key_id)
    key_check = limiter.allow(
        key_rl,
        limit=policy.per_key_per_minute,
        window_seconds=policy.window_seconds,
    )
    if client_ip:
        ip_rl = rate_limit_key_for_ip(tenant_id, client_ip)
        ip_check = limiter.allow(
            ip_rl,
            limit=policy.per_ip_per_minute,
            window_seconds=policy.window_seconds,
        )
        (allowed_key, _), (allowed_ip, _) = await asyncio.gather(key_check, ip_check)
        if not allowed_key:
            return False, "API key rate limit exceeded"
        if not allowed_ip:
            return False, "IP rate limit exceeded"
        return True, None

    allowed, _ = await key_check
    if not allowed:
        return False, "API key rate limit exceeded"
    return True, None
