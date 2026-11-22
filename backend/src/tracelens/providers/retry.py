import asyncio
import random
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from tracelens.config import get_settings
from tracelens.gateway.errors import ProviderError

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def call_with_retry[T](
    fn: Callable[..., Awaitable[T]],
    /,
    *args: Any,
    **kwargs: Any,
) -> T:
    settings = get_settings().retry
    last_error: ProviderError | None = None

    for attempt in range(settings.max_attempts):
        try:
            return await fn(*args, **kwargs)
        except ProviderError as exc:
            last_error = exc
            if exc.status_code not in _RETRYABLE_STATUS:
                raise
            if attempt >= settings.max_attempts - 1:
                raise
            if exc.retry_after_seconds is not None:
                delay = exc.retry_after_seconds
            else:
                delay = min(
                    settings.max_delay_seconds,
                    settings.base_delay_seconds * (2**attempt),
                )
            jitter = random.uniform(0, delay * 0.2)
            await asyncio.sleep(delay + jitter)

    if last_error is not None:
        raise last_error
    msg = "Retry loop exited without result"
    raise RuntimeError(msg)


async def stream_provider_with_retry_placeholder(
    fn: Callable[..., AsyncIterator[dict[str, Any]]],
    /,
    *args: Any,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    async for item in fn(*args, **kwargs):
        yield item


def retry_metadata() -> dict[str, str]:
    settings = get_settings().retry
    return {
        "retry_policy": "jittered_exponential",
        "max_attempts": str(settings.max_attempts),
    }
