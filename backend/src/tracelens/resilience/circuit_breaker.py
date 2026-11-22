import time
from enum import StrEnum

from redis.asyncio import Redis

from tracelens.config import get_settings


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def circuit_scope_key(tenant_id: str, provider: str, model: str) -> str:
    return f"tl:cb:{tenant_id}:{provider}:{model}"


class CircuitBreaker:
    def __init__(self, redis: Redis, scope_key: str) -> None:
        self._redis = redis
        self._scope = scope_key
        self._policy = get_settings().circuit_breaker

    def _state_key(self) -> str:
        return f"{self._scope}:state"

    def _opened_at_key(self) -> str:
        return f"{self._scope}:opened_at"

    def _failures_key(self) -> str:
        return f"{self._scope}:failures"

    async def get_state(self) -> CircuitState:
        raw = await self._redis.get(self._state_key())
        if raw is None:
            return CircuitState.CLOSED
        text = raw.decode() if isinstance(raw, bytes) else str(raw)
        return CircuitState(text)

    async def allow_request(self) -> bool:
        state = await self.get_state()
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.OPEN:
            opened_raw = await self._redis.get(self._opened_at_key())
            if opened_raw is None:
                return False
            opened_at = float(opened_raw)
            if (time.time() - opened_at) >= self._policy.open_seconds:
                await self._redis.set(self._state_key(), CircuitState.HALF_OPEN.value)
                return True
            return False
        return True

    async def record_success(self) -> None:
        state = await self.get_state()
        if state == CircuitState.HALF_OPEN:
            await self._redis.set(self._state_key(), CircuitState.CLOSED.value)
        await self._redis.delete(self._failures_key())
        await self._redis.delete(self._opened_at_key())

    async def record_failure(self) -> None:
        now = time.time()
        window_start = now - self._policy.failure_window_seconds
        failures_key = self._failures_key()
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(failures_key, "-inf", window_start)
            pipe.zadd(failures_key, {f"{now}": now})
            pipe.zcard(failures_key)
            pipe.expire(failures_key, self._policy.failure_window_seconds + 5)
            _, _, count, _ = await pipe.execute()
        if int(count) >= self._policy.failure_threshold:
            await self._redis.set(self._state_key(), CircuitState.OPEN.value)
            await self._redis.set(self._opened_at_key(), str(now))
