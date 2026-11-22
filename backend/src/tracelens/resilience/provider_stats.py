import time

from redis.asyncio import Redis


def stats_scope_key(tenant_id: str, provider: str, model: str) -> str:
    return f"tl:stats:{tenant_id}:{provider}:{model}"


class ProviderStats:
    def __init__(self, redis: Redis, scope_key: str, *, window_seconds: int = 300) -> None:
        self._redis = redis
        self._scope = scope_key
        self._window = window_seconds

    def _latency_key(self) -> str:
        return f"{self._scope}:latency"

    def _error_key(self) -> str:
        return f"{self._scope}:errors"

    async def record_success(self, latency_ms: float) -> None:
        now = time.time()
        window_start = now - self._window
        latency_key = self._latency_key()
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(latency_key, "-inf", window_start)
            pipe.zadd(latency_key, {f"{now}:{latency_ms}": latency_ms})
            pipe.expire(latency_key, self._window + 10)
            await pipe.execute()

    async def record_failure(self) -> None:
        now = time.time()
        window_start = now - self._window
        error_key = self._error_key()
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(error_key, "-inf", window_start)
            pipe.zadd(error_key, {f"{now}": now})
            pipe.expire(error_key, self._window + 10)
            await pipe.execute()

    async def snapshot(self) -> dict[str, float | int]:
        now = time.time()
        window_start = now - self._window
        latency_key = self._latency_key()
        error_key = self._error_key()
        await self._redis.zremrangebyscore(latency_key, "-inf", window_start)
        await self._redis.zremrangebyscore(error_key, "-inf", window_start)
        scored = await self._redis.zrange(latency_key, 0, -1, withscores=True)
        latencies: list[float] = []
        for entry in scored:
            if not isinstance(entry, tuple) or len(entry) != 2:
                continue
            latencies.append(float(entry[1]))
        error_count = await self._redis.zcard(error_key)
        total_requests = len(latencies) + int(error_count)
        p95 = 0.0
        if latencies:
            latencies_sorted = sorted(latencies)
            p95_index = max(0, int(len(latencies_sorted) * 0.95) - 1)
            p95 = latencies_sorted[p95_index]
        error_rate = (error_count / total_requests) if total_requests else 0.0
        return {
            "p95_latency_ms": p95,
            "error_rate": float(error_rate),
            "sample_count": int(total_requests),
        }
