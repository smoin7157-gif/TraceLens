import uuid

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.security.rate_limit import (
    SlidingWindowRateLimiter,
    rate_limit_key_for_api_key,
    rate_limit_key_for_ip,
)


def test_rate_limit_redis_keys_are_tenant_scoped() -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    key_id = uuid.uuid4()
    ip = "203.0.113.10"

    assert rate_limit_key_for_api_key(tenant_a, key_id) != rate_limit_key_for_api_key(
        tenant_b, key_id
    )
    assert rate_limit_key_for_ip(tenant_a, ip) != rate_limit_key_for_ip(tenant_b, ip)
    assert f"tenant:{tenant_a}" in rate_limit_key_for_api_key(tenant_a, key_id)


@pytest.mark.asyncio
async def test_sliding_window_enforces_limit() -> None:
    redis = FakeRedis()
    limiter = SlidingWindowRateLimiter(redis)
    redis_key = "tl:rl:test"

    for _ in range(3):
        allowed, _ = await limiter.allow(redis_key, limit=3, window_seconds=60)
        assert allowed

    allowed, _ = await limiter.allow(redis_key, limit=3, window_seconds=60)
    assert not allowed
