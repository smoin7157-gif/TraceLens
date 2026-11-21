from functools import lru_cache

from redis.asyncio import ConnectionPool, Redis

from tracelens.config import get_settings


@lru_cache
def _pool() -> ConnectionPool:
    settings = get_settings()
    return ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
    )


class RedisClient:
    """Shared async Redis connection pool (cache, queues, limits in later phases)."""

    @classmethod
    def connection(cls) -> Redis:
        return Redis(connection_pool=_pool())

    @classmethod
    async def close(cls) -> None:
        pool = _pool()
        await pool.disconnect()
        _pool.cache_clear()


async def get_redis() -> Redis:
    return RedisClient.connection()
