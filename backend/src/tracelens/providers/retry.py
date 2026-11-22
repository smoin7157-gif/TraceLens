from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any


async def call_provider_with_retry_placeholder[T](
    fn: Callable[..., Awaitable[T]],
    /,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Phase 8 will add jittered backoff, circuit breaker, and Retry-After handling."""
    return await fn(*args, **kwargs)


async def stream_provider_with_retry_placeholder(
    fn: Callable[..., AsyncIterator[dict[str, Any]]],
    /,
    *args: Any,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    """Streaming retry placeholder (phase 8)."""
    async for item in fn(*args, **kwargs):
        yield item


def retry_metadata() -> dict[str, str]:
    return {"retry_policy": "placeholder", "max_attempts": "1"}
