from unittest.mock import AsyncMock, patch

import pytest

from tracelens.gateway.errors import ProviderError
from tracelens.providers.retry import call_with_retry


@pytest.mark.asyncio
async def test_call_with_retry_honors_retry_after() -> None:
    attempts = 0
    sleep_calls: list[float] = []

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderError(
                "slow down",
                status_code=429,
                retry_after_seconds=0.42,
            )
        return "ok"

    with patch("tracelens.providers.retry.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:

        async def _capture(delay: float) -> None:
            sleep_calls.append(delay)

        sleep_mock.side_effect = _capture

        result = await call_with_retry(flaky)

    assert result == "ok"
    assert attempts == 2
    assert len(sleep_calls) == 1
    assert 0.42 <= sleep_calls[0] <= 0.52


@pytest.mark.asyncio
async def test_call_with_retry_does_not_retry_non_retryable() -> None:
    attempts = 0

    async def bad_request() -> str:
        nonlocal attempts
        attempts += 1
        raise ProviderError("nope", status_code=400)

    with pytest.raises(ProviderError):
        await call_with_retry(bad_request)

    assert attempts == 1
