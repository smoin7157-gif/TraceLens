from functools import lru_cache

from redis.asyncio import ConnectionPool, Redis

from tracelens.config import get_settings


@lru_cache
def _pool() -> ConnectionPool:
    settings = get_settings()
    return ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=32,
    )


_client: Redis | None = None


class RedisClient:
    """Shared async Redis connection pool (cache, queues, limits in later phases)."""

    @classmethod
    def connection(cls) -> Redis:
        global _client
        if _client is None:
            _client = Redis(connection_pool=_pool())
        return _client

    @classmethod
    async def close(cls) -> None:
        global _client
        if _client is not None:
            await _client.aclose()
            _client = None
        pool = _pool()
        await pool.disconnect()
        _pool.cache_clear()


async def get_redis() -> Redis:
    return RedisClient.connection()
